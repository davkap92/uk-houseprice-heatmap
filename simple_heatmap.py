import pandas as pd
import json
import glob
import os
import random
from collections import defaultdict

def create_simple_heatmap():
    """Create a simple HTML heatmap using JavaScript and Leaflet"""
    
    # Load sample data
    print("Loading sample data...")
    csv_files = glob.glob(os.path.join("data", "*_link_*.csv"))
    all_data = []
    
    # Process first few files to keep it manageable
    for file_path in csv_files[:10]:
        try:
            print(f"Processing {os.path.basename(file_path)}...")
            df = pd.read_csv(file_path, nrows=200)
            df = df.dropna(subset=['priceper', 'postcode'])
            df = df[df['priceper'] > 0]
            df = df[df['priceper'] < 30000]  # Remove extreme outliers
            
            # Add area name
            area_name = os.path.basename(file_path).replace('_link_26122024.csv', '').replace('_', ' ')
            df['area'] = area_name
            
            all_data.append(df)
            
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            continue
    
    if not all_data:
        print("No data loaded!")
        return
    
    combined_df = pd.concat(all_data, ignore_index=True)
    print(f"Loaded {len(combined_df)} records")
    
    # Group by postcode and calculate averages
    postcode_data = combined_df.groupby('postcode').agg({
        'priceper': 'mean',
        'area': 'first',
        'year': 'max'
    }).reset_index()
    
    # Simple postcode to coordinates mapping (approximate)
    uk_coords = {
        'E': [51.5074, -0.1278],   # London
        'W': [51.4816, -3.1791],   # Wales
        'S': [55.9533, -3.1883],   # Scotland
        'N': [54.5973, -5.9301],   # Northern Ireland
        'M': [53.4808, -2.2426],   # Manchester
        'B': [52.4862, -1.8904],   # Birmingham
        'L': [53.4084, -2.9916],   # Liverpool
        'LS': [53.8008, -1.5491],  # Leeds
        'SH': [53.3811, -1.4701],  # Sheffield
    }
    
    # Prepare data for JavaScript
    heatmap_points = []
    for _, row in postcode_data.iterrows():
        postcode = row['postcode']
        price = row['priceper']
        area = row['area']
        
        # Extract postcode area
        postcode_area = ''.join([c for c in postcode.split()[0] if c.isalpha()])
        
        # Get approximate coordinates
        if postcode_area in uk_coords:
            lat, lon = uk_coords[postcode_area]
            # Add some variation
            import random
            lat += random.uniform(-0.2, 0.2)
            lon += random.uniform(-0.2, 0.2)
        else:
            # Default to London with variation
            lat = 51.5074 + random.uniform(-0.3, 0.3)
            lon = -0.1278 + random.uniform(-0.3, 0.3)
        
        heatmap_points.append({
            'lat': lat,
            'lon': lon,
            'price': price,
            'postcode': postcode,
            'area': area
        })
    
    print(f"Prepared {len(heatmap_points)} points for visualization")
    
    # Create HTML content
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>UK House Price Heatmap</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    
    <!-- Leaflet CSS -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
    
    <!-- Leaflet Heat Plugin -->
    <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/leaflet.heat@0.2.0/dist/leaflet-heat.js"></script>
    
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
        }}
        
        .header {{
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            text-align: center;
        }}
        
        .stats {{
            display: flex;
            justify-content: space-around;
            background-color: #ecf0f1;
            padding: 15px;
        }}
        
        .stat-item {{
            text-align: center;
        }}
        
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        }}
        
        .stat-label {{
            font-size: 14px;
            color: #7f8c8d;
        }}
        
        #map {{
            height: 600px;
            width: 100%;
        }}
        
        .controls {{
            padding: 20px;
            background-color: #f8f9fa;
        }}
        
        .legend {{
            position: absolute;
            bottom: 30px;
            right: 30px;
            background: white;
            padding: 10px;
            border-radius: 5px;
            box-shadow: 0 0 15px rgba(0,0,0,0.2);
            z-index: 1000;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            margin: 5px 0;
        }}
        
        .legend-color {{
            width: 20px;
            height: 20px;
            margin-right: 10px;
            border-radius: 3px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>UK House Price per sqm Heatmap</h1>
        <p>Interactive visualization of property prices across the UK</p>
    </div>
    
    <div class="stats">
        <div class="stat-item">
            <div class="stat-value">{len(heatmap_points):,}</div>
            <div class="stat-label">Properties</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">£{combined_df['priceper'].mean():.0f}</div>
            <div class="stat-label">Avg Price/sqm</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">£{combined_df['priceper'].min():.0f}</div>
            <div class="stat-label">Min Price/sqm</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">£{combined_df['priceper'].max():.0f}</div>
            <div class="stat-label">Max Price/sqm</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{combined_df['area'].nunique()}</div>
            <div class="stat-label">Areas</div>
        </div>
    </div>
    
    <div class="controls">
        <p><strong>Instructions:</strong> The heatmap shows house price intensity with red indicating higher prices and blue indicating lower prices. Click on points to see detailed information.</p>
    </div>
    
    <div id="map"></div>
    
    <div class="legend">
        <h4>Price per sqm</h4>
        <div class="legend-item">
            <div class="legend-color" style="background: #0000ff;"></div>
            <span>Low (£{combined_df['priceper'].quantile(0.2):.0f})</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #00ff00;"></div>
            <span>Medium (£{combined_df['priceper'].quantile(0.5):.0f})</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #ffff00;"></div>
            <span>High (£{combined_df['priceper'].quantile(0.8):.0f})</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #ff0000;"></div>
            <span>Very High (£{combined_df['priceper'].quantile(0.95):.0f})</span>
        </div>
    </div>

    <script>
        // Initialize map
        var map = L.map('map').setView([54.5, -2.0], 6);
        
        // Add tile layer
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '© OpenStreetMap contributors'
        }}).addTo(map);
        
        // Data
        var heatmapData = {json.dumps(heatmap_points)};
        
        // Prepare heat data
        var heatPoints = heatmapData.map(function(point) {{
            // Normalize price for heat intensity (0-1)
            var minPrice = {combined_df['priceper'].min()};
            var maxPrice = {combined_df['priceper'].max()};
            var intensity = (point.price - minPrice) / (maxPrice - minPrice);
            return [point.lat, point.lon, Math.max(0.1, intensity)];
        }});
        
        // Add heatmap
        var heat = L.heatLayer(heatPoints, {{
            radius: 20,
            blur: 15,
            maxZoom: 17,
            gradient: {{
                0.0: 'blue',
                0.2: 'cyan',
                0.4: 'lime',
                0.6: 'yellow',
                0.8: 'orange',
                1.0: 'red'
            }}
        }}).addTo(map);
        
        // Add markers for high-value properties
        var highValueThreshold = {combined_df['priceper'].quantile(0.9)};
        heatmapData.forEach(function(point) {{
            if (point.price >= highValueThreshold) {{
                var marker = L.circleMarker([point.lat, point.lon], {{
                    radius: 5,
                    fillColor: 'red',
                    color: 'darkred',
                    weight: 1,
                    opacity: 0.8,
                    fillOpacity: 0.6
                }});
                
                marker.bindPopup(
                    '<strong>' + point.area + '</strong><br>' +
                    'Postcode: ' + point.postcode + '<br>' +
                    'Price per sqm: £' + Math.round(point.price) + '<br>' +
                    '<em>High-value property</em>'
                );
                
                marker.addTo(map);
            }}
        }});
        
        // Add some regular markers for context
        var samplePoints = heatmapData.filter(function(point, index) {{
            return index % 10 === 0; // Every 10th point
        }});
        
        samplePoints.forEach(function(point) {{
            var marker = L.circleMarker([point.lat, point.lon], {{
                radius: 3,
                fillColor: 'blue',
                color: 'darkblue',
                weight: 1,
                opacity: 0.6,
                fillOpacity: 0.4
            }});
            
            marker.bindPopup(
                '<strong>' + point.area + '</strong><br>' +
                'Postcode: ' + point.postcode + '<br>' +
                'Price per sqm: £' + Math.round(point.price)
            );
            
            marker.addTo(map);
        }});
        
        console.log('Loaded ' + heatmapData.length + ' data points');
    </script>
</body>
</html>
"""
    
    # Save HTML file
    with open('uk_house_price_heatmap_simple.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("Simple heatmap created: uk_house_price_heatmap_simple.html")
    print("Open this file in your web browser to view the interactive map!")

if __name__ == "__main__":
    create_simple_heatmap()
