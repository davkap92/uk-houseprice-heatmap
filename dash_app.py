import dash
from dash import dcc, html, Input, Output, callback
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import glob
import os
from collections import defaultdict
import pickle
from postcode_dataset import UKPostcodeDataset

class UKHousePriceDashboard:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.df = None
        
        # Initialize the UK postcode dataset for accurate geocoding
        print("Initializing UK postcode dataset...")
        self.postcode_geocoder = UKPostcodeDataset()
        
        # Load postcode data (this will use cached data if available)
        if not self.postcode_geocoder.load_postcode_data():
            print("Warning: Failed to load postcode dataset. Coordinates may be inaccurate.")
            self.postcode_geocoder = None

    def get_coordinates(self, postcode):
        """Get accurate coordinates for a postcode using the real dataset"""
        if self.postcode_geocoder:
            return self.postcode_geocoder.get_coordinates(postcode)
        else:
            # Fallback to Central London if dataset not available
            return 51.5074, -0.1278

    def load_data(self, max_files=350, max_rows_per_file=180000):
        """Load and process house price data"""
        # data from https://data.london.gov.uk/dataset/house-price-per-square-metre-in-england-and-wales/
        csv_files = glob.glob(os.path.join(self.data_dir, "*_link_*.csv"))
        print(f"Found {len(csv_files)} CSV files")

        all_data = []

        for file_path in csv_files[:max_files]:
            try:
                print(f"Processing {os.path.basename(file_path)}...")
                df = pd.read_csv(file_path, nrows=max_rows_per_file)

                # Clean data
                df = df.dropna(subset=['priceper', 'postcode'])
                df = df[df['priceper'] > 0]
                df = df[df['priceper'] < 50000]  # Remove extreme outliers
                
                # Filter for houses sold in the last 2 years (2024-2025)
                if 'year' in df.columns:
                    df = df[df['year'] >= 2024]
                elif 'dateoftransfer' in df.columns:
                    # Convert dateoftransfer to datetime and filter
                    df['dateoftransfer'] = pd.to_datetime(df['dateoftransfer'], errors='coerce')
                    cutoff_date = pd.Timestamp('2024-01-01')
                    df = df[df['dateoftransfer'] >= cutoff_date]

                # Add area name from filename
                area_name = os.path.basename(file_path).replace('_link_26122024.csv', '').replace('_', ' ')
                df['area'] = area_name

                all_data.append(df)

            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                continue

        if all_data:
            self.df = pd.concat(all_data, ignore_index=True)

            # Add coordinates using real postcode dataset
            print("Adding accurate coordinates using postcode dataset...")
            coords_list = []
            successful = 0
            
            for postcode in self.df['postcode']:
                coords = self.get_coordinates(postcode)
                if coords and coords != (51.5074, -0.1278):  # Not the fallback
                    coords_list.append(coords)
                    successful += 1
                else:
                    coords_list.append((None, None))

            self.df['lat'] = [c[0] for c in coords_list]
            self.df['lon'] = [c[1] for c in coords_list]

            # Remove rows with no coordinates
            self.df = self.df.dropna(subset=['lat', 'lon'])

            print(f"Loaded {len(self.df)} records with accurate coordinates")
            print(f"Successfully geocoded {successful} postcodes")
            return self.df

        return pd.DataFrame()

    def create_app(self):
        """Create Dash application"""
        app = dash.Dash(__name__)

        # Load data
        if self.df is None:
            self.load_data()

        app.layout = html.Div([
            html.Div([
                html.H1("🏠 UK House Price Heat Map (Recent Sales 2024-2025)", 
                       style={'text-align': 'center', 'color': '#2c3e50', 'margin-bottom': '30px'}),
                
                html.Div([
                    html.Div([
                        html.Label("Price Range (£/sqm):", style={'font-weight': 'bold', 'margin-bottom': '5px'}),
                        dcc.RangeSlider(
                            id='price-range-slider',
                            min=int(self.df['priceper'].min()) if len(self.df) > 0 else 0,
                            max=int(self.df['priceper'].max()) if len(self.df) > 0 else 10000,
                            value=[2000, 8000],
                            marks={i: f'£{i:,}' for i in range(0, 15000, 2000)},
                            step=100,
                            tooltip={"placement": "bottom", "always_visible": True}
                        ),
                    ], style={'width': '48%', 'display': 'inline-block', 'margin-right': '4%'}),
                    
                    html.Div([
                        html.Label("Area Filter:", style={'font-weight': 'bold', 'margin-bottom': '5px'}),
                        dcc.Dropdown(
                            id='area-dropdown',
                            options=[{'label': 'All Areas', 'value': 'all'}] + 
                                   [{'label': area, 'value': area} for area in sorted(self.df['area'].unique())],
                            value='all',
                            clearable=False
                        ),
                    ], style={'width': '48%', 'display': 'inline-block'}),
                ], style={'display': 'flex', 'justify-content': 'space-between', 'margin-bottom': '30px'}),
                
                # Main content area
                html.Div([
                    # Left panel - Map
                    html.Div([
                        dcc.Graph(id='price-map', style={'height': '600px'})
                    ], style={
                        'width': '65%', 
                        'display': 'inline-block', 
                        'vertical-align': 'top',
                        'padding-right': '20px'
                    }),
                    
                    # Right panel - Charts
                    html.Div([
                        dcc.Graph(id='price-distribution', style={'height': '280px', 'margin-bottom': '20px'}),
                        dcc.Graph(id='area-comparison', style={'height': '280px'})
                    ], style={
                        'width': '35%', 
                        'display': 'inline-block', 
                        'vertical-align': 'top'
                    }),
                ], style={'display': 'flex'}),
                
                # Bottom stats
                html.Div(id='summary-stats', style={
                    'margin-top': '30px',
                    'padding': '20px',
                    'background-color': '#f8f9fa',
                    'border-radius': '8px',
                    'text-align': 'center'
                })
                
            ], style={
                'max-width': '1400px',
                'margin': '0 auto',
                'padding': '20px',
                'font-family': 'Arial, sans-serif'
            })
        ])

        @app.callback(
            [Output('price-map', 'figure'),
             Output('price-distribution', 'figure'),
             Output('area-comparison', 'figure'),
             Output('summary-stats', 'children')],
            [Input('price-range-slider', 'value'),
             Input('area-dropdown', 'value')]
        )
        def update_dashboard(price_range, selected_area):
            # Filter data
            filtered_df = self.df[
                (self.df['priceper'] >= price_range[0]) & 
                (self.df['priceper'] <= price_range[1])
            ]
            
            if selected_area != 'all':
                filtered_df = filtered_df[filtered_df['area'] == selected_area]
            
            if len(filtered_df) == 0:
                # Return empty figures if no data
                empty_fig = go.Figure()
                empty_fig.add_annotation(text="No data available for selected filters", 
                                       showarrow=False, 
                                       x=0.5, y=0.5, 
                                       xref="paper", yref="paper")
                return empty_fig, empty_fig, empty_fig, "No data available"
            
            # Create heat map with postcode district aggregation
            map_fig = go.Figure()
            
            # Extract postcode districts (e.g., NW3, SW1, etc.) and aggregate
            def extract_postcode_district(postcode):
                if pd.isna(postcode) or not postcode:
                    return None
                # Split by space and take first part, or first 3-4 chars if no space
                parts = str(postcode).strip().upper().split()
                if len(parts) >= 1:
                    district = parts[0]
                    # Remove digits from end to get just the area code
                    import re
                    match = re.match(r'^([A-Z]{1,2}\d{1,2}[A-Z]?)', district)
                    if match:
                        return match.group(1)
                return None
            
            # Add postcode district column
            filtered_df['postcode_district'] = filtered_df['postcode'].apply(extract_postcode_district)
            
            # Aggregate by postcode district
            district_df = filtered_df.groupby('postcode_district').agg({
                'priceper': ['mean', 'count'],
                'lat': 'mean',
                'lon': 'mean',
                'area': 'first'
            }).reset_index()
            
            # Flatten column names
            district_df.columns = ['postcode_district', 'avg_price', 'property_count', 'lat', 'lon', 'area']
            
            # Filter out districts with too few properties for reliable averages
            district_df = district_df[district_df['property_count'] >= 3]
            
            print(f"Showing {len(district_df)} postcode districts (aggregated from {len(filtered_df)} properties)")
            
            # Add scatter plot with color scale
            map_fig.add_trace(go.Scattermapbox(
                lat=district_df['lat'],
                lon=district_df['lon'],
                mode='markers',
                marker=dict(
                    size=district_df['property_count'].apply(lambda x: min(max(x/2 + 8, 8), 20)),  # Size based on property count
                    color=district_df['avg_price'],
                    colorscale='RdYlBu_r',
                    showscale=True,
                    colorbar=dict(title="Avg Price/sqm (£)"),
                    opacity=0.7
                ),
                text=[f"District: {district}<br>Avg Price: £{price:,.0f}/sqm<br>Properties: {count}<br>Area: {area}" 
                      for district, price, count, area in zip(district_df['postcode_district'], 
                                                            district_df['avg_price'], 
                                                            district_df['property_count'],
                                                            district_df['area'])],
                hovertemplate='%{text}<extra></extra>'
            ))
            
            # Calculate map center
            center_lat = district_df['lat'].median()
            center_lon = district_df['lon'].median()
            
            map_fig.update_layout(
                mapbox={
                    'style': "open-street-map",
                    'center': {'lat': center_lat, 'lon': center_lon},
                    'zoom': 10
                },
                margin={"r":0,"t":30,"l":0,"b":0},
                title="House Price Heat Map (By Postcode District)",
                # Performance optimizations
                uirevision='constant',  # Preserve zoom/pan state
                dragmode='pan'
            )
            
            # Price distribution histogram
            dist_fig = px.histogram(
                filtered_df, 
                x='priceper', 
                nbins=30,
                title='Price Distribution',
                labels={'priceper': 'Price per sqm (£)', 'count': 'Number of Properties'}
            )
            dist_fig.update_layout(margin={"r":0,"t":30,"l":20,"b":20})
            
            # Area comparison
            area_stats = filtered_df.groupby('area')['priceper'].agg(['mean', 'count']).reset_index()
            area_stats = area_stats[area_stats['count'] >= 5]  # Only areas with 5+ properties
            area_stats = area_stats.sort_values('mean', ascending=True).tail(10)  # Top 10
            
            area_fig = px.bar(
                area_stats,
                x='mean',
                y='area',
                title='Average Price by Area (Top 10)',
                labels={'mean': 'Average Price/sqm (£)', 'area': 'Area'},
                orientation='h'
            )
            area_fig.update_layout(margin={"r":0,"t":30,"l":100,"b":20})
            
            # Summary statistics
            avg_price = filtered_df['priceper'].mean()
            median_price = filtered_df['priceper'].median()
            total_properties = len(filtered_df)
            districts_shown = len(district_df)
            
            summary = html.Div([
                html.H3("📊 Summary Statistics", style={'color': '#2c3e50', 'margin-bottom': '15px'}),
                html.Div([
                    html.Div([
                        html.H4(f"£{avg_price:,.0f}", style={'color': '#e74c3c', 'margin': '0'}),
                        html.P("Average Price/sqm", style={'margin': '5px 0'})
                    ], style={'text-align': 'center', 'flex': '1'}),
                    html.Div([
                        html.H4(f"£{median_price:,.0f}", style={'color': '#3498db', 'margin': '0'}),
                        html.P("Median Price/sqm", style={'margin': '5px 0'})
                    ], style={'text-align': 'center', 'flex': '1'}),
                    html.Div([
                        html.H4(f"{total_properties:,}", style={'color': '#27ae60', 'margin': '0'}),
                        html.P("Total Properties", style={'margin': '5px 0'})
                    ], style={'text-align': 'center', 'flex': '1'}),
                    html.Div([
                        html.H4(f"{districts_shown}", style={'color': '#f39c12', 'margin': '0'}),
                        html.P("Districts Shown", style={'margin': '5px 0'})
                    ], style={'text-align': 'center', 'flex': '1'}),
                ], style={'display': 'flex', 'justify-content': 'space-around'})
            ])
            
            return map_fig, dist_fig, area_fig, summary

        return app


def main():
    """Run the dashboard"""
    dashboard = UKHousePriceDashboard()
    app = dashboard.create_app()
    
    print("🚀 Starting UK House Price Heat Map Dashboard...")
    print("📍 Open your browser to: http://localhost:8050")
    print("💡 Using accurate postcode coordinates from real UK dataset")
    print("📅 Showing only houses sold in the last 2 years (2024-2025)")

    app.run(debug=True, host='0.0.0.0', port=8050)


if __name__ == "__main__":
    main()
