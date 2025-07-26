#!/bin/bash

echo "Setting up UK House Price Heatmap Application..."

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv heatmap_env

# Activate virtual environment
echo "Activating virtual environment..."
source heatmap_env/bin/activate

# Install requirements
echo "Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Setup complete!"
echo ""
echo "To run the application:"
echo "1. Activate the virtual environment: source heatmap_env/bin/activate"
echo "2. Run the basic heatmap generator: python heatmap_generator.py"
echo "3. Or run the interactive dashboard: python dash_app.py"
echo ""
echo "The dashboard will be available at: http://localhost:8050"
