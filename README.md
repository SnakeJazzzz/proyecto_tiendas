# Store Performance Visualization System

An interactive visualization system for monitoring and analyzing store performance across Mexico. This project uses Python, Pandas, Folium and web technologies to create an engaging and informative dashboard of store metrics.

## Features

- **Interactive Maps**: Visualize store performance metrics across Mexican states
- **Multi-Month Analysis**: Compare performance across different months
- **Automatic Geocoding**: Locate stores accurately with full address information
- **Performance Categories**: Quickly identify high and low-performing areas with intuitive color coding
- **Top/Bottom Performers**: See at a glance which stores are excelling or struggling
- **Heatmaps**: Visualize performance density across geographical regions
- **Dashboard**: Comprehensive web dashboard with charts and statistics
- **Flexible Metrics**: Switch between different performance indicators (sales, orders, ticket size)

## Project Structure

```
proyecto_tiendas/
│
├── data/                           # Data folder
│   ├── datosEne2025.csv            # January 2025 data
│   ├── datosFeb2025.csv            # February 2025 data
│   └── mexico_estados.geojson      # GeoJSON file with Mexican states
│
├── src/                            # Source code
│   ├── __init__.py                 # Package initialization
│   ├── data_processing.py          # Data loading and processing functions
│   ├── geocoding.py                # Address geocoding functions
│   └── map_visualization.py        # Map and visualization creation
│
├── dashboard/                      # Generated dashboard
│   ├── index.html                  # Main dashboard HTML
│   └── maps/                       # Generated map HTML files
│
├── maps/                           # Generated standalone maps
│
├── dashboard_template.html         # Template for dashboard generation
├── dashboard_generator.py          # Script to generate dashboard
├── main.py                         # Main script to run analysis
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

## Setup Instructions

### 1. Environment Setup

```bash
# Clone the repository or unzip the project files
# Navigate to the project directory
cd proyecto_tiendas

# Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the dependencies
pip install -r requirements.txt
```

### 2. Data Preparation

Place your data files in the `data` folder:

- Monthly data files should follow the naming convention `datosEne2025.csv`, `datosFeb2025.csv`, etc.
- Make sure the GeoJSON file `mexico_estados.geojson` is in the data folder

### 3. Running the Analysis

To generate maps and visualizations for all available months:

```bash
python main.py
```

With custom options:

```bash
# Specify data folder, metric to visualize, and output folder
python main.py --data_folder data --metric var_ventas --output_folder maps

# Force re-geocoding (useful if you've updated store addresses)
python main.py --force_geocode
```

### 4. Generating the Dashboard

After running the analysis, generate the interactive dashboard:

```bash
# First make sure main.py has been run to generate the maps
python -c "
from src import data_processing
from dashboard_generator import generate_dashboard

# Load data
monthly_data, combined_df = data_processing.load_multiple_months('data')

# Generate dashboard
generate_dashboard(monthly_data, combined_df, 'dashboard')
"
```

### 5. Viewing the Dashboard

Open the generated `dashboard/index.html` file in your web browser to interact with the visualization dashboard.

## Usage Guide

### Dashboard Controls

- **Month Selector**: Switch between different months or view combined data
- **Metric Selector**: Choose between Sales Variation, Order Variation, or Ticket Variation
- **View Selector**: Switch between Map, Heatmap, or Combined view

### Map Features

- **State Colors**: States are colored based on performance (red for negative, green for positive)
- **Store Markers**: Click on store markers to see detailed performance metrics
- **Layer Control**: Toggle different data layers on/off (top right corner)
- **Zoom Controls**: Zoom in/out to focus on specific regions

### Leaderboards

The dashboard includes leaderboards showing:
- **Top 5 Performers**: Best performing stores for the selected metric
- **Bottom 5 Performers**: Worst performing stores for the selected metric

### Performance Categories

Performance is categorized as follows:
- **Red** (-100% to -10%): Significant underperformance
- **Orange** (-9% to -1%): Mild underperformance
- **Yellow** (0% to 5%): Neutral or slight improvement
- **Light Green** (6% to 19%): Good performance
- **Dark Green** (20%+): Excellent performance

## Extending the Project

### Adding More Months

Simply add new CSV files to the `data` directory following the naming convention (e.g., `datosMar2025.csv`). Run the main script again to process the new data.

### Adding New Metrics

To add new performance metrics:
1. Update the `read_and_clean_data` function in `src/data_processing.py` to include the new metric
2. Add appropriate visualizations in `src/map_visualization.py`
3. Update the dashboard template to include the new metric

### Customizing Colors and Thresholds

The performance category thresholds and colors can be adjusted in the `categorize_performance` function in `src/data_processing.py`.

## Troubleshooting

### Geocoding Issues

- If stores are not appearing on the map, check the geocoding cache file for missing coordinates
- Try using the `--force_geocode` option to refresh all geocoding data
- Ensure store addresses are complete with street, city, state, and postal code

### Map Rendering Problems

- If maps don't display properly, check your internet connection (needed for loading map tiles)
- Try a different web browser if you encounter rendering issues
- For large datasets, increase the browser memory limit if available

## Contact Information

For questions or support, please contact your project manager or developer.