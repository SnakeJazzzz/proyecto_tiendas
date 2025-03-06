import os
import argparse
from src import data_processing
from src.geocoding import GeocodingManager
from src import map_visualization
import pandas as pd
import shutil

def main():
    """
    Main function to orchestrate the store performance visualization workflow
    """
    # Set up argument parser for command-line options
    parser = argparse.ArgumentParser(description='Generate interactive maps for store performance data')
    parser.add_argument('--data_folder', type=str, default='data', help='Folder containing the CSV data files')
    parser.add_argument('--geojson_path', type=str, default=os.path.join('data', 'mexico_estados.geojson'), 
                        help='Path to the GeoJSON file with Mexican states')
    parser.add_argument('--output_folder', type=str, default='maps', help='Folder to save the generated maps')
    parser.add_argument('--metric', type=str, default='var_ventas', help='Primary metric for visualization (var_ventas, var_ov, var_ticket)')
    parser.add_argument('--cache_file', type=str, default='geocoding_cache.json', help='File to cache geocoding results')
    parser.add_argument('--force_geocode', action='store_true', help='Force re-geocoding even if coordinates exist in cache')
    parser.add_argument('--update_dashboard', action='store_true', help='Update dashboard after generating maps')
    
    args = parser.parse_args()
    
    print(f"Starting store performance visualization process...")
    print(f"Data folder: {args.data_folder}")
    print(f"Output folder: {args.output_folder}")
    
    # Create output folder if it doesn't exist
    os.makedirs(args.output_folder, exist_ok=True)
    
    # Load data from all months
    print(f"Loading data from {args.data_folder}...")
    monthly_data, combined_df = data_processing.load_multiple_months(args.data_folder)
    
    if not monthly_data:
        print(f"No data files found in {args.data_folder}. Exiting.")
        return
    
    print(f"Loaded data for {len(monthly_data)} months: {', '.join(monthly_data.keys())}")
    
    # Initialize geocoding manager
    geocoding_manager = GeocodingManager(cache_file=args.cache_file)
    
    # Process each month's data
    for month, df in monthly_data.items():
        print(f"\nProcessing data for {month}...")
        
        # Geocode stores if coordinates are missing
        if args.force_geocode or 'latitud' not in df.columns or 'longitud' not in df.columns:
            print(f"Geocoding stores for {month}...")
            monthly_data[month] = geocoding_manager.geocode_dataframe(df)
        else:
            print(f"Using existing geocoding data for {month}")
        
        # Add performance categories
        monthly_data[month] = data_processing.add_performance_categories(monthly_data[month])
        
        # Get top and bottom performers for this month
        top_stores = data_processing.get_top_performers(monthly_data[month], metric=args.metric, n=5, by_state=False)
        bottom_stores = data_processing.get_bottom_performers(monthly_data[month], metric=args.metric, n=5, by_state=False)
        
        print(f"\nTop 5 stores for {month} ({args.metric}):")
        for i, (idx, row) in enumerate(top_stores.iterrows()):
            print(f"  {i+1}. {row['Sucursal']}: {row[args.metric]:.1f}%")
        
        print(f"\nBottom 5 stores for {month} ({args.metric}):")
        for i, (idx, row) in enumerate(bottom_stores.iterrows()):
            print(f"  {i+1}. {row['Sucursal']}: {row[args.metric]:.1f}%")
    
    # Update combined DataFrame with geocoding results
    combined_df = pd.concat([monthly_data[month] for month in monthly_data], ignore_index=True)
    
    # Generate various map visualizations
    print(f"\nGenerating maps...")
    
    # Create interactive maps
    map_paths = map_visualization.crear_mapa_interactivo(
        monthly_data, 
        combined_df, 
        args.geojson_path, 
        output_folder=args.output_folder
    )
    
    # Update dashboard if requested or --update_dashboard is specified
    if args.update_dashboard or True:  # Always update for this version
        update_dashboard(monthly_data, combined_df)
    
    print("\nProcess completed successfully!")
    print(f"All outputs saved to {args.output_folder}")
    print("\nAvailable maps:")
    for name, path in map_paths.items():
        print(f"  - {name}: {path}")
    
    print("\nTo view the dashboard, open: dashboard/index.html in your web browser")

def update_dashboard(monthly_data, combined_df, output_folder='dashboard'):
    """
    Update the dashboard with the latest map data
    
    Parameters:
    -----------
    monthly_data : dict
        Dictionary with month as key and DataFrame as value
    combined_df : pd.DataFrame
        Combined DataFrame with all months
    output_folder : str, optional
        Folder to save the dashboard (default: 'dashboard')
    """
    print("\nUpdating dashboard...")
    
    # Ensure dashboard folder exists
    os.makedirs(output_folder, exist_ok=True)
    
    # Create maps folder inside dashboard if it doesn't exist
    dashboard_maps_folder = os.path.join(output_folder, 'maps')
    os.makedirs(dashboard_maps_folder, exist_ok=True)
    
    # Copy all HTML files from maps folder to dashboard/maps
    source_maps_folder = 'maps'
    copied_files = []
    
    # Check if source maps folder exists
    if os.path.exists(source_maps_folder):
        # Get list of HTML files
        map_files = [f for f in os.listdir(source_maps_folder) if f.endswith('.html')]
        
        # Copy each file
        for map_file in map_files:
            source_path = os.path.join(source_maps_folder, map_file)
            dest_path = os.path.join(dashboard_maps_folder, map_file)
            try:
                shutil.copy(source_path, dest_path)
                copied_files.append(map_file)
            except Exception as e:
                print(f"Error copying {map_file}: {e}")
    
    if copied_files:
        print(f"Copied {len(copied_files)} map files to {dashboard_maps_folder}")
    else:
        print(f"No map files found to copy to dashboard")
    
    # Generate dashboard HTML
    try:
        from dashboard_generator import generate_dashboard
        dashboard_path = generate_dashboard(monthly_data, combined_df, output_folder)
        print(f"Dashboard updated at {dashboard_path}")
    except Exception as e:
        print(f"Error generating dashboard: {e}")
        print("You can still view the maps directly from the maps folder")

if __name__ == "__main__":
    main()