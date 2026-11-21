import pandas as pd
import numpy as np
import folium
from folium.plugins import HeatMap, Search
from folium.template import Template
from folium.utilities import JsCode
import glob
import os
import time
import pickle
from collections import defaultdict
import branca.colormap as cm
import re
from html import escape
from pathlib import Path
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
        """Create interactive heatmap with postcode district markers.
        Adds a hidden GeoJSON layer purely for search across postcode district and area.
        No tooltips or popups (per user request)."""
        if not heatmap_data:
            print("No data available for heatmap")
            return None

        print("Creating heatmap...")

        # Determine map center
        if len(district_df) > 0:
            center_lat = district_df['lat'].median()
            center_lon = district_df['lon'].median()
        else:
            center_lat, center_lon = 51.5074, -0.1278

        m = folium.Map(location=[center_lat, center_lon], zoom_start=10, tiles='OpenStreetMap')

        # Title
        title_html = """
        <div style="position: fixed; top: 10px; left: 50%; transform: translateX(-50%); width: 400px; 
                    background-color: rgba(255,255,255,0.9); border:2px solid #2c3e50; z-index:9999; 
                    font-size:16px; padding: 10px; text-align: center; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
        <h3 style="margin: 0; color: #2c3e50;">🏠 UK House Price Heat Map</h3>
        <p style="margin: 5px 0 0 0; font-size: 12px; color: #666;">Recent Sales (2024-2025) by Postcode District</p>
        </div>
        """
        m.get_root().html.add_child(folium.Element(title_html))

        # Price range
        prices = [pt[2] for pt in heatmap_data]
        max_price = max(prices)
        min_price = min(prices)
        print(f"Price range for heatmap: £{min_price:,.0f} - £{max_price:,.0f}")

        # Hidden GeoJSON for search
        features = []
        for _, row in district_df.iterrows():
            lat = row['lat']; lon = row['lon']
            district = row['postcode_district']
            avg_price = row['avg_price']; property_count = row['property_count']; area = row['area']
            price_range = max_price - min_price if max_price > min_price else 1
            # Color scale reuse
            thresholds = [0.9,0.8,0.7,0.6,0.5,0.4,0.3,0.2,0.1]
            colors = ['#FF0000','#FF4000','#FF8000','#FFFF00','#80FF00','#00FF00','#00FF80','#00FFFF','#0080FF']
            color = '#0000FF'
            for t,c in zip(thresholds,colors):
                if avg_price >= min_price + price_range * t:
                    color = c
                    break
            radius = min(max(property_count / 2 + 5, 5), 15)
            search_text = f"{district} {area}".strip()
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": {
                    "district": district,
                    "area": area,
                    "search_text": search_text,
                    "avg_price": f"£{avg_price:,.0f}/sqm",
                    "property_count": int(property_count),
                    "color": color,
                    "radius": radius
                }
            })

        geojson = {"type": "FeatureCollection", "features": features}

        def style_function(feature):
            return {
                'color': feature['properties']['color'],
                'fillColor': feature['properties']['color'],
                'fillOpacity': 0.0,
                'opacity': 0.0,
                'weight': 0
            }

        gj = folium.GeoJson(geojson, name="Districts", style_function=style_function)
        gj.add_to(m)

        Search(layer=gj,
               search_label='search_text',
               placeholder='Search postcode or area...',
               collapsed=False,
               position='topright').add_to(m)

        # Add circle markers (clickable bubbles) without default pin icon.
        # Size/color based on avg price and property count.
        for f in geojson["features"]:
            props = f["properties"]
            lat = f["geometry"]["coordinates"][1]
            lon = f["geometry"]["coordinates"][0]
            popup_html = (f"<b>{props['district']}</b><br>" 
                          f"{props['area']}<br>" 
                          f"{props['avg_price']}<br>" 
                          f"Properties: {props['property_count']}")
            folium.CircleMarker(
                location=[lat, lon],
                radius=props['radius'],
                color=props['color'],
                fill=True,
                fill_color=props['color'],
                fill_opacity=0.6,
                opacity=0.8,
                weight=1,
                popup=folium.Popup(popup_html, max_width=250)
            ).add_to(m)

        # Hide the default blue pin produced by Search (Leaflet markers in this control)
        hide_pin_css = """
        <style>
        .leaflet-marker-icon, .leaflet-marker-shadow { display: none !important; }
        </style>
        """
        m.get_root().html.add_child(folium.Element(hide_pin_css))

        # Heatmap layer
        HeatMap(heatmap_data,
                min_opacity=0.4,
                max_zoom=18,
                radius=20,
                blur=15,
                gradient={
                    0.0:'#000080',0.1:'#0000FF',0.2:'#0080FF',0.3:'#00FFFF',0.4:'#00FF80',
                    0.5:'#00FF00',0.6:'#80FF00',0.7:'#FFFF00',0.8:'#FF8000',0.9:'#FF4000',1.0:'#FF0000'
                }).add_to(m)

        # Legend
        colormap = cm.LinearColormap(colors=['#000080','#0000FF','#0080FF','#00FFFF','#00FF80','#00FF00',
                                             '#80FF00','#FFFF00','#FF8000','#FF4000','#FF0000'],
                                     vmin=min_price, vmax=max_price,
                                     caption='Average House Price per sqm (£)')
        colormap = colormap.to_step(n=10)
        colormap.caption = 'Average House Price per sqm (£)'
        colormap.add_to(m)

        # Stats box
        stats_html = f"""
        <div style="position: fixed; top: 80px; left: 10px; width: 220px; height: 120px; 
                    background-color: white; border:2px solid grey; z-index:9999; font-size:12px; padding: 10px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
        <h4 style=\"margin: 0 0 10px 0; color: #2c3e50;\">📍 District Summary</h4>
        <div style=\"line-height: 1.4;\">
        <b>Postcode Districts:</b> {len(district_df):,}<br>
        <b>Total Properties:</b> {district_df['property_count'].sum():,}<br>
        <b>Average Price:</b> £{district_df['avg_price'].mean():,.0f}/sqm<br>
        <b>Price Range:</b> £{district_df['avg_price'].min():,.0f} - £{district_df['avg_price'].max():,.0f}
        </div></div>"""
        m.get_root().html.add_child(folium.Element(stats_html))

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

class DistrictSearch(Search):
    """Search existing district markers without adding an overlapping marker."""

    _template = Template("""
        {% macro script(this, kwargs) %}
        var {{ this.get_name() }} = new L.Control.Search({
            layer: {{ this.layer.get_name() }},
            propertyName: {{ this.search_label|tojson }},
            textPlaceholder: {{ this.placeholder|tojson }},
            position: {{ this.position|tojson }},
            collapsed: {{ this.collapsed|tojson }},
            zoom: {{ this.search_zoom|tojson }},
            initial: false,
            marker: false
        });
        {{ this.get_name() }}.on('search:locationfound', ({ layer }) => layer.openPopup());
        {{ this._parent.get_name() }}.addControl({{ this.get_name() }});
        {% endmacro %}
    """)


def create_2025_district_map(districts, output_file):
    """Map published district prices and the number of matched sales."""
    if districts.empty:
        raise ValueError("The 2025 postcode district snapshot is empty.")

    price_scale = cm.StepColormap(
        colors=["#2166ac", "#4393c3", "#92c5de", "#f7f7b8",
                "#fddbc7", "#f4a582", "#d6604d", "#b2182b", "#67001f"],
        index=[0, 1500, 2500, 3500, 4500, 6000, 8000, 10000, 15000, 30000],
        vmin=0,
        vmax=30000,
        caption="Sale price per m² (January 2026 pounds)",
        tick_labels=[0, 5000, 10000, 15000, 20000, 25000, 30000],
    )
    price_scale.width = 300
    features = []
    for row in districts.itertuples(index=False):
        district = escape(row.postcode_district)
        place = escape(row.place)
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [row.longitude, row.latitude]},
            "properties": {
                "district": district,
                "place": place,
                "search_text": f"{district} {place}".strip(),
                "price": f"£{row.adjusted_price_per_sqm:,}/m²",
                "matched_sales": f"{row.matched_sales:,}",
                "style": {"fillColor": price_scale.rgb_hex_str(row.adjusted_price_per_sqm)},
            },
        })

    price_map = folium.Map(
        location=[districts.latitude.median(), districts.longitude.median()],
        zoom_start=6, tiles="OpenStreetMap", prefer_canvas=True,
    )
    price_map.fit_bounds(
        [[districts.latitude.min(), districts.longitude.min()],
         [districts.latitude.max(), districts.longitude.max()]],
        padding=[16, 16],
    )
    district_layer = folium.GeoJson(
        {"type": "FeatureCollection", "features": features},
        name="Postcode districts",
        marker=folium.CircleMarker(
            radius=6, color="#334155", weight=1, fill=True, fill_opacity=1,
        ),
        on_each_feature=JsCode("""
            function (feature, layer) {
                const { district, place, price, matched_sales } = feature.properties;
                const outline = { color: layer.options.color, weight: layer.options.weight };
                layer.bindPopup(`<strong>${district}</strong> · ${place}<br>
                    <span>${price}</span> in January 2026 pounds<br>
                    ${matched_sales} matched sales`);
                layer.on('popupopen', () => layer.setStyle({ color: '#e03', weight: 2 }));
                layer.on('popupclose', () => layer.setStyle(outline));
            }
        """),
    ).add_to(price_map)
    DistrictSearch(
        layer=district_layer,
        search_label="search_text",
        search_zoom=12,
        placeholder="Search district or place",
        position="topright",
    ).add_to(price_map)
    price_scale.add_to(price_map)

    page = price_map.get_root()
    page.title = "2025 house prices per m² in England and Wales"
    page.header.add_child(folium.Element(f"""
        <style>
          body {{ display: flex; flex-direction: column; }}
          #{price_map.get_name()} {{ flex: 1; height: auto; min-height: 260px; }}
          .map-summary {{ padding: 10px 16px; background: #fff; color: #233247; font: 14px/1.45 system-ui, sans-serif; }}
          .map-summary h1 {{ margin: 0 0 3px; font-size: clamp(17px, 3vw, 23px); }}
          .map-summary p {{ margin: 0; }}
          .map-summary details {{ margin-top: 3px; }}
          .map-summary summary {{ cursor: pointer; }}
          .map-summary a {{ color: #175b91; text-decoration: underline; }}
          .leaflet-control.legend {{ background: #fff; border-radius: 4px; }}
          .leaflet-control-search input.search-input {{ width: 235px; max-width: calc(100vw - 84px); font-size: 14px; }}
        </style>
    """))
    page.html.add_child(folium.Element(f"""
        <header class="map-summary">
          <h1>{page.title}</h1>
          <p>{len(districts):,} postcode districts · {districts.matched_sales.sum():,} matched sales · January 2026 pounds</p>
          <details>
            <summary>Data and method</summary>
            <p><a href="https://houseprices.huwdiprose.co.uk/">Huw Diprose</a> links HM Land Registry sale prices to domestic EPC floor areas.
            Each district's price is the total adjusted sale value divided by total floor area.
            The source includes districts with at least 10 matched sales in 2025.</p>
            <p>Contains HM Land Registry and EPC data © Crown copyright. Postal boundaries © GeoLytix copyright and database right 2012.
            Contains Ordnance Survey and National Statistics data © Crown copyright and database right, and Royal Mail data © Royal Mail copyright and database right.
            <a href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/">Open Government Licence</a>.</p>
          </details>
        </header>
    """), index=0)
    page_html = page.render()
    Path(output_file).write_text(
        "\n".join(line.rstrip() for line in page_html.splitlines()) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    project_dir = Path(__file__).resolve().parent
    districts = pd.read_csv(project_dir / "data" / "postcode_district_prices_2025.csv", keep_default_na=False)
    output_file = project_dir / "uk_house_price_heatmap.html"
    create_2025_district_map(districts, output_file)
    print(f"Saved the 2025 map to {output_file}")
