# UK House Price Heatmap Application

An interactive map of 2025 house sale prices per square metre in England and Wales.

## Demo
https://davkap92.github.io/uk-houseprice-heatmap/uk_house_price_heatmap.html

## Features

- **2025 District Map**: Compare sale prices by postcode district. Search by district or place and select a marker for its price and sale count.
- **Data Filtering**: Filter by area, price range, and other criteria
- **Statistical Dashboard**: View price distributions and area comparisons
- **Multiple Visualization Options**: Choose between Folium-based maps and Plotly dashboards

## Quick Start

### 1. Setup Environment

Use Python 3.12 with the pinned dependencies.

Make the setup script executable and run it:
```bash
chmod +x setup.sh
./setup.sh
```

Or manually:
```bash
python3.12 -m venv heatmap_env
source heatmap_env/bin/activate
pip install -r requirements.txt
```

### 2. Run the Application

#### Option A: 2025 Postcode District Map (Folium)
```bash
source heatmap_env/bin/activate
python heatmap_generator.py
```
Open `uk_house_price_heatmap.html` in a browser. The generator uses the included 2025 snapshot. The browser needs internet access for map tiles and libraries.

#### Option B: Interactive Dashboard (Dash/Plotly)
```bash
source heatmap_env/bin/activate
python dash_app.py
```
Then open http://localhost:8050 in your browser.

## Dash Transaction Data Format

Download the individual sale files from the [London Datastore](https://data.london.gov.uk/dataset/house-price-per-square-metre-in-england-and-wales/).

Your CSV files should contain at minimum:
- `priceper`: Price per square meter
- `postcode`: UK postcode
- `year`: Year of transaction
- `propertytype`: Type of property
- Additional fields like `duration`, `price`, etc. are also supported

## Configuration

### Adjusting Dash Data Loading
- Modify `max_files` and `max_rows_per_file` in `dash_app.py` to control how much transaction data loads
- For better performance with large datasets, reduce these values
- For comprehensive analysis, increase them (but expect longer loading times)

### Customizing Visualization
- **Map colours** can be set in `create_2025_district_map`.
- **Map extent** comes from the district marker locations in the snapshot.

## File Structure

```
uk_price_heatmap_app/
├── data/postcode_district_prices_2025.csv # 2025 district price snapshot
├── heatmap_generator.py           # Folium district map generator
├── dash_app.py                   # Interactive Dash dashboard
├── requirements.txt              # Python dependencies
├── setup.sh                     # Setup script
├── README.md                    # This file
└── postcode_coords_cache.pkl    # Cached coordinates (auto-generated)
```

## Performance Tips

1. **Start Small**: Begin with a subset of your data to test the application
2. **Caching**: The app caches postcode coordinates to speed up subsequent runs
3. **Sampling**: Use the sampling parameters to work with manageable data sizes
4. **Browser Performance**: Large datasets may slow down browser rendering

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure the virtual environment is activated
2. **Memory Issues**: Reduce `max_files` and `max_rows_per_file` parameters
3. **Slow Loading**: Enable coordinate caching and use data sampling
4. **Map Not Displaying**: Check your internet connection for map tiles

### Data Issues

1. **Missing Coordinates**: The app estimates coordinates based on postcode prefixes
2. **Invalid Prices**: Extreme outliers are automatically filtered out
3. **Missing Data**: Rows with missing essential fields are automatically removed

## Customization Examples

### Changing Price Filters
```python
# In the data loading functions, modify:
df = df[df['priceper'] < 20000]  # Remove prices above £20k/sqm
df = df[df['priceper'] > 1000]   # Remove prices below £1k/sqm
```

### Adding New Visualizations
The Dash app is modular - you can easily add new charts by:
1. Creating a new graph component in the layout
2. Adding it to the callback outputs
3. Implementing the visualization logic

### Different Map Styles
For the Folium version, you can change map tiles:
```python
folium.Map(tiles='CartoDB positron')  # Light theme
folium.Map(tiles='Stamen Terrain')    # Terrain view
```

## Data Sources

The 2025 Folium map uses [Huw Diprose's annual postcode district CSV](https://houseprices.huwdiprose.co.uk/price_per_sqm_yearly_postcode_district.csv). The snapshot contains 390,115 matched sales in 2,111 districts. The source includes districts with at least 10 matched sales that year.

Each price is the sum of inflation-adjusted sale prices divided by the sum of the floor areas. Prices are in January 2026 pounds. The source links Land Registry Price Paid Data to domestic Energy Performance Certificates. See the [source methodology and attribution](https://houseprices.huwdiprose.co.uk/).

The snapshot joins the 2025 prices and sale counts to the publisher's [GeoLytix district boundaries](https://houseprices.huwdiprose.co.uk/postcode_districts.geojson) by postcode district. Each marker uses a point inside the largest polygon for its district. Place names come from the boundary file. The source includes E20 sales in E15.

Contains HM Land Registry and EPC data © Crown copyright. Postal boundaries © GeoLytix copyright and database right 2012. Contains Ordnance Survey and National Statistics data © Crown copyright and database right, and Royal Mail data © Royal Mail copyright and database right. [Open Government Licence](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).

## License

Open source - feel free to modify and distribute.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Verify your data format matches the expected structure
3. Ensure all dependencies are properly installed
