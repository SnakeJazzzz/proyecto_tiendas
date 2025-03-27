# Store Performance Dashboard

## Overview
This is a simplified version of the Store Performance Visualization System. It consolidates the functionality into a single HTML file that can be opened in any modern web browser, without the need for complex Python dependencies or multiple generated files.

## Getting Started

### Option 1: Using the HTML File Directly (Recommended)
1. Open `dashboard.html` in any modern web browser (Chrome, Firefox, Edge, etc.)
2. Use the file upload controls to load your data files:
   - Upload your monthly CSV files (`datosEne2025.csv`, `datosFeb2025.csv`, etc.)
   - Upload the `mexico_estados.geojson` file for the map visualization

### Option 2: Using Python for Geocoding (Optional)
If you need to add location coordinates to stores that don't have them:

1. Make sure you have Python installed with the required packages:

2. Run the data processing script:

3. This will create geocoded versions of your CSV files in the data folder
4. Open `dashboard.html` and load these geocoded files

## Using the Dashboard

### Loading Data
1. Use the "Cargar archivos CSV" button to select one or more monthly data files
2. Use the "Cargar GeoJSON" button to load the Mexican states geographical data
3. Once files are loaded, the dashboard will automatically process and display the data

### Interacting with the Dashboard
- **Month Selector**: Choose between individual months or "Todos los Meses" (all months combined)
- **Metric Selector**: Select which metric to visualize:
- Variación Ventas (Sales Variation)
- Variación Órdenes (Orders Variation) 
- Variación Ticket (Ticket Size Variation)
- **View Selector**: Choose between "Mapa" (normal map) or "Mapa de Calor" (heatmap)

### Dashboard Sections
- **Map**: Visualizes store performance geographically. States are colored based on their average performance for the selected metric.
- **General Statistics**: Shows average values for all three metrics
- **Top/Bottom 5**: Displays the best and worst performing stores
- **Performance by Format**: Chart showing performance by store format
- **Performance by Region**: Chart showing performance by region
- **Performance by State**: Table listing all states and their performance metrics

## Data File Requirements

### CSV Files
The monthly data files should have the following columns:
- `Formato`: Store format (e.g., Devlyn, Coppel, Sears)
- `Zona`: Region/zone
- `Distrito`: District
- `Sucursal`: Store name
- Sales variation column (one of the following):
- `$ Crec% MT 2025 vs 2024`
- `Venta Neta MT 2024 vs 2023`
- Orders variation column (one of the following):
- `Ordenes Crec% MT 2025 vs 2024`
- `OV MT 2024 vs 2023`
- Ticket variation column (one of the following):
- `Ticket Crec% MT 2025 vs 2024`
- `Ticket MT 2024 vs 2023`
- `Estado`: State name (important for map visualization)
- `latitud` and `longitud`: Store coordinates (optional, for displaying stores on map)

## Troubleshooting

### Map Not Displaying
- Ensure the GeoJSON file has been loaded successfully
- Check that the state names in your CSV data match those in the GeoJSON file

### Missing Store Locations
If stores aren't appearing on the map:
- Make sure your CSV files include `latitud` and `longitud` columns
- Use the Python script with the `--geocode` option to add coordinates

### Browser Compatibility
This dashboard is compatible with modern browsers (Chrome, Firefox, Edge, Safari)
It does not support Internet Explorer.