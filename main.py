import os
import argparse
import shutil
from src import data_processing
from src.geocoding import GeocodingManager

def main():
    """
    Main function to prepare data for the dashboard
    """
    parser = argparse.ArgumentParser(description='Prepare data for store performance dashboard')
    parser.add_argument('--data_folder', type=str, default='data', help='Folder containing the CSV data files')
    parser.add_argument('--geocode', action='store_true', help='Update geocoding for stores')
    parser.add_argument('--cache_file', type=str, default='geocoding_cache.json', help='File to cache geocoding results')
    
    args = parser.parse_args()
    
    print(f"Processing store data from {args.data_folder}...")
    
    # Load data
    monthly_data, combined_df = data_processing.load_multiple_months(args.data_folder)
    
    if args.geocode:
        # Geocode stores if requested
        geocoder = GeocodingManager(cache_file=args.cache_file)
        for month, df in monthly_data.items():
            print(f"Geocoding stores for {month}...")
            monthly_data[month] = geocoder.geocode_dataframe(df)
            
            # Save geocoded data back to CSV
            output_file = os.path.join(args.data_folder, f"datos{month[:3]}2025_geocoded.csv")
            monthly_data[month].to_csv(output_file, index=False)
            print(f"Saved geocoded data to {output_file}")
    
    print("\nData processing completed successfully.")
    print(f"Total records processed: {len(combined_df)}")
    print(f"Months detected: {', '.join(monthly_data.keys())}")
    print("\nUse the dashboard.html file to visualize the data.")

if __name__ == "__main__":
    main()