# UK House Price Heatmap Application

An interactive visualization tool for UK house price per square meter data.

## Features

- **Interactive Heatmap**: Visualize house prices across the UK with color-coded intensity
- **Data Filtering**: Filter by area, price range, and other criteria
- **Statistical Dashboard**: View price distributions and area comparisons
- **Multiple Visualization Options**: Choose between Folium-based maps and Plotly dashboards

## Quick Start

### 1. Setup Environment

Make the setup script executable and run it:
```bash
chmod +x setup.sh
./setup.sh
```

Or manually:
```bash
python3 -m venv heatmap_env
source heatmap_env/bin/activate
pip install -r requirements.txt
```

### 2. Run the Application

#### Option A: Basic Heatmap Generator (Folium)
```bash
source heatmap_env/bin/activate
python heatmap_generator.py
```
This creates an HTML file `uk_house_price_heatmap.html` that you can open in your browser.

#### Option B: Interactive Dashboard (Dash/Plotly)
```bash
source heatmap_env/bin/activate
python dash_app.py
```
Then open http://localhost:8050 in your browser.

## Data Format

Your CSV files should contain at minimum:
- `priceper`: Price per square meter
- `postcode`: UK postcode
- `year`: Year of transaction
- `propertytype`: Type of property
- Additional fields like `duration`, `price`, etc. are also supported

## Configuration

### Adjusting Data Loading
- Modify `max_files` and `max_rows_per_file` in the scripts to control how much data is loaded
- For better performance with large datasets, reduce these values
- For comprehensive analysis, increase them (but expect longer loading times)

### Customizing Visualization
- **Color schemes**: Modify the gradient colors in the heatmap functions
- **Map center**: Adjust the UK center coordinates for different focus areas
- **Clustering**: Enable/disable point clustering for better performance

## File Structure

```
uk_price_heatmap_app/
├── data/                          # Your CSV data files
├── heatmap_generator.py           # Basic Folium heatmap generator
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

This application works with UK house price data in CSV format. Ensure your data includes:
- Price per square meter calculations
- Valid UK postcodes
- Transaction dates
- Property type information

## License

Open source - feel free to modify and distribute.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Verify your data format matches the expected structure
3. Ensure all dependencies are properly installed
