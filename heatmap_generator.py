import pandas as pd
import numpy as np
import folium
from folium.plugins import HeatMap
import glob
import os
import time
import pickle
from collections import defaultdict
import branca.colormap as cm
import re
from postcode_dataset import UKPostcodeDataset

class UKHousePriceHeatMap:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.postcode_geocoder = UKPostcodeDataset()
        self.coords_cache_file = "postcode_coords_cache.pkl"
        
        # Load postcode data (this will use cached data if available)
        print("Initializing UK postcode dataset...")
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

    def extract_postcode_district(self, postcode):
        """Extract postcode district (e.g., NW3, SW1) from full postcode"""
        if pd.isna(postcode) or not postcode:
            return None
        # Split by space and take first part, or first 3-4 chars if no space
        parts = str(postcode).strip().upper().split()
        if len(parts) >= 1:
            district = parts[0]
            # Remove digits from end to get just the area code
            match = re.match(r'^([A-Z]{1,2}\d{1,2}[A-Z]?)', district)
            if match:
                return match.group(1)
        return None
    
    def load_data(self, max_files=73, max_rows_per_file=1000):
        """Load and process house price data with postcode district aggregation"""
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
            combined_df = pd.concat(all_data, ignore_index=True)

            # Add coordinates using real postcode dataset
            print("Adding accurate coordinates using postcode dataset...")
            coords_list = []
            successful = 0
            
            for postcode in combined_df['postcode']:
                coords = self.get_coordinates(postcode)
                if coords and coords != (51.5074, -0.1278):  # Not the fallback
                    coords_list.append(coords)
                    successful += 1
                else:
                    coords_list.append((None, None))

            combined_df['lat'] = [c[0] for c in coords_list]
            combined_df['lon'] = [c[1] for c in coords_list]

            # Remove rows with no coordinates
            combined_df = combined_df.dropna(subset=['lat', 'lon'])

            print(f"Successfully geocoded {successful}/{len(combined_df)} records")
            return combined_df

        return pd.DataFrame()
    
    def prepare_heatmap_data(self, df, sample_size=None):
        """Prepare data for heatmap visualization using postcode district aggregation"""
        print("Preparing heatmap data with postcode district aggregation...")
        
        if len(df) == 0:
            print("No data to process")
            return [], pd.DataFrame()
        
        # Extract postcode districts and aggregate
        df['postcode_district'] = df['postcode'].apply(self.extract_postcode_district)
        
        # Aggregate by postcode district
        district_df = df.groupby('postcode_district').agg({
            'priceper': ['mean', 'count'],
            'lat': 'mean',
            'lon': 'mean',
            'area': 'first'
        }).reset_index()
        
        # Flatten column names
        district_df.columns = ['postcode_district', 'avg_price', 'property_count', 'lat', 'lon', 'area']
        
        # Filter out districts with too few properties for reliable averages
        district_df = district_df[district_df['property_count'] >= 3]
        
        print(f"Aggregated {len(df)} properties into {len(district_df)} postcode districts")
        
        # Prepare heatmap data
        heatmap_data = []
        
        for _, row in district_df.iterrows():
            lat = row['lat']
            lon = row['lon']
            avg_price = row['avg_price']
            property_count = row['property_count']
            district = row['postcode_district']
            
            if pd.notna(lat) and pd.notna(lon):
                # Add multiple points for districts with more properties (for better heat visualization)
                weight = min(property_count / 5, 3)  # Max weight of 3
                for _ in range(max(1, int(weight))):
                    heatmap_data.append([lat, lon, avg_price])
        
        print(f"Prepared {len(heatmap_data)} data points for heatmap")
        return heatmap_data, district_df
    
    def create_heatmap(self, heatmap_data, district_df, output_file="uk_house_price_heatmap.html"):
        """Create interactive heatmap with postcode district markers"""
        if not heatmap_data:
            print("No data available for heatmap")
            return None
        
        print("Creating heatmap...")
        
        # Calculate map center from district data
        if len(district_df) > 0:
            center_lat = district_df['lat'].median()
            center_lon = district_df['lon'].median()
        else:
            center_lat, center_lon = 51.5074, -0.1278  # London fallback
        
        # Create base map
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=10,
            tiles='OpenStreetMap'
        )
        
        # Add a title to the map
        title_html = """
        <div style="position: fixed; 
                    top: 10px; left: 50%; transform: translateX(-50%); width: 400px; 
                    background-color: rgba(255,255,255,0.9); border:2px solid #2c3e50; z-index:9999; 
                    font-size:16px; padding: 10px; text-align: center; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
        <h3 style="margin: 0; color: #2c3e50;">🏠 UK House Price Heat Map</h3>
        <p style="margin: 5px 0 0 0; font-size: 12px; color: #666;">Recent Sales (2024-2025) by Postcode District</p>
        </div>
        """
        m.get_root().html.add_child(folium.Element(title_html))
        
        # Prepare data for heatmap - using actual prices for better color mapping
        prices = [point[2] for point in heatmap_data]
        max_price = max(prices)
        min_price = min(prices)
        
        print(f"Price range for heatmap: £{min_price:,.0f} - £{max_price:,.0f}")
        
        # Add heatmap layer with prices directly (not normalized intensity)
        HeatMap(
            heatmap_data,  # Use actual [lat, lon, price] data
            min_opacity=0.3,
            max_zoom=18,
            radius=20,
            blur=15,
            gradient={
                0.0: 'blue',
                0.2: 'cyan', 
                0.4: 'lime',
                0.6: 'yellow',
                0.8: 'orange',
                1.0: 'red'
            }
        ).add_to(m)
        
        # Add postcode district markers
        for _, row in district_df.iterrows():
            lat = row['lat']
            lon = row['lon']
            district = row['postcode_district']
            avg_price = row['avg_price']
            property_count = row['property_count']
            area = row['area']
            
            # Color based on price
            if avg_price >= np.percentile(district_df['avg_price'], 80):
                color = 'red'
            elif avg_price >= np.percentile(district_df['avg_price'], 60):
                color = 'orange'
            elif avg_price >= np.percentile(district_df['avg_price'], 40):
                color = 'yellow'
            else:
                color = 'green'
            
            # Size based on property count
            radius = min(max(property_count / 2 + 5, 5), 15)
            
            folium.CircleMarker(
                location=[lat, lon],
                radius=radius,
                popup=f"<b>{district}</b><br>Avg: £{avg_price:,.0f}/sqm<br>Properties: {property_count}<br>Area: {area}",
                color=color,
                fillColor=color,
                fillOpacity=0.6,
                weight=2
            ).add_to(m)
        
        # Add a better colormap legend that matches the heatmap
        colormap = cm.LinearColormap(
            colors=['blue', 'cyan', 'lime', 'yellow', 'orange', 'red'],
            vmin=min_price,
            vmax=max_price,
            caption='Average House Price per sqm (£)'
        )
        
        # Add custom tick labels for better readability
        colormap = colormap.to_step(n=6)
        colormap.caption = 'Average House Price per sqm (£)'
        colormap.add_to(m)
        
        # Add improved statistics to the map (positioned on the left to avoid legend overlap)
        stats_html = f"""
        <div style="position: fixed; 
                    top: 80px; left: 10px; width: 220px; height: 120px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:12px; padding: 10px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
        <h4 style="margin: 0 0 10px 0; color: #2c3e50;">📍 District Summary</h4>
        <div style="line-height: 1.4;">
        <b>Postcode Districts:</b> {len(district_df):,}<br>
        <b>Total Properties:</b> {district_df['property_count'].sum():,}<br>
        <b>Average Price:</b> £{district_df['avg_price'].mean():,.0f}/sqm<br>
        <b>Price Range:</b> £{district_df['avg_price'].min():,.0f} - £{district_df['avg_price'].max():,.0f}
        </div>
        </div>
        """
        m.get_root().html.add_child(folium.Element(stats_html))
        
        # Save map
        m.save(output_file)
        print(f"Heatmap saved as {output_file}")
        
        return m
    
    def generate_statistics(self, df):
        """Generate statistics about the data"""
        stats = {
            'total_records': len(df),
            'unique_postcodes': df['postcode'].nunique(),
            'price_range': {
                'min': df['priceper'].min(),
                'max': df['priceper'].max(),
                'mean': df['priceper'].mean(),
                'median': df['priceper'].median()
            },
            'property_types': df['propertytype'].value_counts().to_dict() if 'propertytype' in df.columns else {}
        }
        return stats

if __name__ == "__main__":
    # Create heatmap
    heatmap = UKHousePriceHeatMap()
    
    # Load data
    df = heatmap.load_data(max_files=300, max_rows_per_file=150000)
    
    if not df.empty:
        # Generate statistics
        stats = heatmap.generate_statistics(df)
        print("\nDataset Statistics:")
        print(f"Total records: {stats['total_records']:,}")
        print(f"Unique postcodes: {stats['unique_postcodes']:,}")
        print(f"Price per sqm range: £{stats['price_range']['min']:.0f} - £{stats['price_range']['max']:.0f}")
        print(f"Average price per sqm: £{stats['price_range']['mean']:.0f}")
        
        # Prepare and create heatmap
        heatmap_data, district_df = heatmap.prepare_heatmap_data(df)
        
        if heatmap_data:
            map_obj = heatmap.create_heatmap(heatmap_data, district_df)
            print("\nHeatmap created successfully!")
            print("Open 'uk_house_price_heatmap.html' in your browser to view the interactive map.")
            print(f"Map shows {len(district_df)} postcode districts aggregated from {len(df)} properties")
        else:
            print("Could not create heatmap - no valid coordinate data found")
    else:
        print("No data loaded")
