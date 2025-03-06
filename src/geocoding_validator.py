import pandas as pd
import json
import folium
import os
import argparse
from tqdm import tqdm
from geopy.distance import geodesic

def load_geocoding_cache(cache_file):
    """
    Load geocoding cache from JSON file
    
    Parameters:
    -----------
    cache_file : str
        Path to geocoding cache file
        
    Returns:
    --------
    dict
        Geocoding cache dictionary
    """
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            print(f"Warning: Could not load cache from {cache_file}. Starting with empty cache.")
            return {}
    else:
        return {}

def analyze_geocoding_results(df, cache_file=None, distance_threshold=10.0):
    """
    Analyze geocoding results for quality and completeness
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with geocoded store data
    cache_file : str, optional
        Path to geocoding cache file (default: None)
    distance_threshold : float, optional
        Threshold in kilometers for detecting potential issues (default: 10.0)
        
    Returns:
    --------
    dict
        Analysis results
    """
    # Initialize results
    results = {
        'total_stores': len(df),
        'geocoded_stores': 0,
        'geocoding_success_rate': 0.0,
        'stores_by_state': {},
        'geocoding_by_state': {},
        'potential_issues': [],
        'state_performance': {}
    }
    
    # Count geocoded stores
    has_coords = df[pd.notna(df['latitud']) & pd.notna(df['longitud'])].copy()
    results['geocoded_stores'] = len(has_coords)
    results['geocoding_success_rate'] = len(has_coords) / len(df) * 100 if len(df) > 0 else 0
    
    # Analyze by state
    state_column = 'Estado' if 'Estado' in df.columns else 'estado'
    if state_column in df.columns:
        state_counts = df[state_column].value_counts().to_dict()
        results['stores_by_state'] = state_counts
        
        # Calculate geocoding success rate by state
        for state in state_counts:
            state_df = df[df[state_column] == state]
            state_geocoded = state_df[pd.notna(state_df['latitud']) & pd.notna(state_df['longitud'])]
            success_rate = len(state_geocoded) / len(state_df) * 100 if len(state_df) > 0 else 0
            results['geocoding_by_state'][state] = {
                'total': len(state_df),
                'geocoded': len(state_geocoded),
                'success_rate': success_rate
            }
            
            # Categorize state performance
            if success_rate >= 95:
                performance = 'Excellent'
            elif success_rate >= 80:
                performance = 'Good'
            elif success_rate >= 60:
                performance = 'Fair'
            else:
                performance = 'Poor'
            
            results['state_performance'][state] = performance
    
    # Check for potential issues
    # 1. Stores in the same state that are far from the state centroid
    if len(has_coords) > 0 and state_column in df.columns:
        # Calculate centroids for each state
        state_centroids = {}
        for state in results['stores_by_state']:
            state_stores = has_coords[has_coords[state_column] == state]
            if len(state_stores) > 0:
                state_centroids[state] = (
                    state_stores['latitud'].mean(),
                    state_stores['longitud'].mean()
                )
        
        # Check for outliers
        for idx, row in has_coords.iterrows():
            if row[state_column] in state_centroids:
                store_coords = (row['latitud'], row['longitud'])
                centroid = state_centroids[row[state_column]]
                distance = geodesic(store_coords, centroid).kilometers
                
                # Flag stores that are more than the threshold away from their state's centroid
                if distance > distance_threshold:
                    results['potential_issues'].append({
                        'store': row['Sucursal'],
                        'state': row[state_column],
                        'coords': store_coords,
                        'centroid_distance_km': distance,
                        'issue_type': 'Far from state centroid'
                    })
    
    # 2. Check for repeated coordinates (could indicate default placement)
    coord_counts = has_coords.groupby(['latitud', 'longitud']).size().reset_index(name='count')
    duplicated_coords = coord_counts[coord_counts['count'] > 1]
    
    for _, row in duplicated_coords.iterrows():
        same_coord_stores = has_coords[(has_coords['latitud'] == row['latitud']) & 
                                        (has_coords['longitud'] == row['longitud'])]
        
        # If multiple stores share exact coordinates, they might be incorrectly geocoded
        if len(same_coord_stores) > 1:
            store_names = same_coord_stores['Sucursal'].tolist()
            results['potential_issues'].append({
                'coords': (row['latitud'], row['longitud']),
                'count': row['count'],
                'stores': store_names,
                'issue_type': 'Multiple stores with identical coordinates'
            })
    
    # Check the cache if provided
    if cache_file:
        cache = load_geocoding_cache(cache_file)
        
        # Check how many stores have cached coordinates
        cached_addresses = set(cache.keys())
        
        # Count addresses with no valid coordinates in cache
        failed_cache_entries = sum(1 for addr, data in cache.items() 
                                   if data.get('lat') is None or data.get('lon') is None)
        
        results['cache_stats'] = {
            'total_cached_addresses': len(cache),
            'failed_cache_entries': failed_cache_entries,
            'cache_failure_rate': failed_cache_entries / len(cache) * 100 if len(cache) > 0 else 0
        }
    
    return results

def create_validation_map(df, analysis_results, output_html='geocoding_validation.html'):
    """
    Create a validation map showing geocoded stores and potential issues
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with store data
    analysis_results : dict
        Analysis results from analyze_geocoding_results
    output_html : str, optional
        Path to save the HTML map (default: 'geocoding_validation.html')
        
    Returns:
    --------
    folium.Map
        Folium map object
    """
    # Create a map centered on Mexico
    m = folium.Map(location=[23.6345, -102.5528], zoom_start=5, 
                   tiles='cartodb positron')
    
    # Add a title
    title_html = """
    <h3 align="center" style="font-size:16px"><b>Geocoding Validation Map</b></h3>
    """
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Create feature groups for different categories
    valid_stores = folium.FeatureGroup(name="Valid Geocoding")
    issue_stores = folium.FeatureGroup(name="Potential Issues")
    
    # Add markers for all geocoded stores
    geocoded_df = df[pd.notna(df['latitud']) & pd.notna(df['longitud'])].copy()
    
    # Track stores with issues for exclusion from the valid group
    issue_store_names = set()
    
    # Add markers for stores with potential issues
    for issue in analysis_results['potential_issues']:
        if 'store' in issue:  # Single store issue
            store_row = df[df['Sucursal'] == issue['store']]
            if not store_row.empty:
                issue_store_names.add(issue['store'])
                
                # Create popup content
                popup_content = f"""
                <div style="min-width: 180px">
                    <b>{issue['store']}</b><br>
                    <b>Issue:</b> {issue['issue_type']}<br>
                    <b>Distance from centroid:</b> {issue['centroid_distance_km']:.1f} km<br>
                </div>
                """
                
                folium.Marker(
                    location=[store_row['latitud'].iloc[0], store_row['longitud'].iloc[0]],
                    popup=folium.Popup(popup_content, max_width=300),
                    tooltip=f"ISSUE: {issue['store']}",
                    icon=folium.Icon(color='red', icon='warning-sign', prefix='glyphicon')
                ).add_to(issue_stores)
        
        elif 'stores' in issue:  # Multi-store issue (duplicate coordinates)
            for store_name in issue['stores']:
                issue_store_names.add(store_name)
            
            # Create popup content for duplicate coordinates
            popup_content = f"""
            <div style="min-width: 180px">
                <b>Issue:</b> {issue['issue_type']}<br>
                <b>Stores:</b><br>
                <ul style="padding-left: 20px; margin-bottom: 0;">
                    {"".join(f"<li>{store}</li>" for store in issue['stores'])}
                </ul>
            </div>
            """
            
            folium.Marker(
                location=[issue['coords'][0], issue['coords'][1]],
                popup=folium.Popup(popup_content, max_width=300),
                tooltip=f"ISSUE: {len(issue['stores'])} stores at same location",
                icon=folium.Icon(color='orange', icon='warning-sign', prefix='glyphicon')
            ).add_to(issue_stores)
    
    # Add valid stores (those without identified issues)
    for idx, row in geocoded_df.iterrows():
        if row['Sucursal'] not in issue_store_names:
            # Create popup content
            popup_content = f"""
            <div style="min-width: 180px">
                <b>{row['Sucursal']}</b><br>
                <b>Formato:</b> {row.get('Formato', 'N/A')}<br>
                <b>Estado:</b> {row.get('Estado', row.get('estado', 'N/A'))}<br>
                <b>Coordenadas:</b> {row['latitud']:.6f}, {row['longitud']:.6f}
            </div>
            """
            
            folium.Marker(
                location=[row['latitud'], row['longitud']],
                popup=folium.Popup(popup_content, max_width=300),
                tooltip=row['Sucursal'],
                icon=folium.Icon(color='green', icon='ok', prefix='glyphicon')
            ).add_to(valid_stores)
    
    # Add the feature groups to the map
    valid_stores.add_to(m)
    issue_stores.add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Add summary info box
    summary_html = f"""
    <div style="position: fixed; 
                bottom: 50px; 
                right: 50px; 
                width: 250px; 
                height: auto; 
                padding: 10px; 
                background-color: white; 
                border-radius: 5px; 
                box-shadow: 0 0 15px rgba(0,0,0,0.2); 
                z-index: 1000;">
        <h4 style="margin-top: 0;">Geocoding Summary</h4>
        <table style="width: 100%;">
            <tr>
                <td>Total Stores:</td>
                <td style="text-align: right;">{analysis_results['total_stores']}</td>
            </tr>
            <tr>
                <td>Geocoded:</td>
                <td style="text-align: right;">{analysis_results['geocoded_stores']} 
                    ({analysis_results['geocoding_success_rate']:.1f}%)</td>
            </tr>
            <tr>
                <td>Potential Issues:</td>
                <td style="text-align: right;">{len(analysis_results['potential_issues'])}</td>
            </tr>
        </table>
    </div>
    """
    
    m.get_root().html.add_child(folium.Element(summary_html))
    
    # Save the map
    m.save(output_html)
    print(f"Validation map saved to {output_html}")
    
    return m

def generate_report(analysis_results, output_file='geocoding_report.md'):
    """
    Generate a detailed report of the geocoding analysis
    
    Parameters:
    -----------
    analysis_results : dict
        Analysis results from analyze_geocoding_results
    output_file : str, optional
        Path to save the report (default: 'geocoding_report.md')
    """
    # Create report content
    report = f"""# Geocoding Quality Report

## Summary Statistics
- **Total Stores**: {analysis_results['total_stores']}
- **Successfully Geocoded**: {analysis_results['geocoded_stores']} ({analysis_results['geocoding_success_rate']:.1f}%)
- **Potential Issues**: {len(analysis_results['potential_issues'])}

## Geocoding by State

| State | Total Stores | Geocoded | Success Rate | Performance |
|-------|--------------|----------|--------------|-------------|
"""
    
    # Add state details
    for state, stats in sorted(analysis_results['geocoding_by_state'].items()):
        performance = analysis_results['state_performance'].get(state, 'Unknown')
        report += f"| {state} | {stats['total']} | {stats['geocoded']} | {stats['success_rate']:.1f}% | {performance} |\n"
    
    # Add potential issues section
    report += """
## Potential Issues

"""
    
    # Group issues by type
    issues_by_type = {}
    for issue in analysis_results['potential_issues']:
        issue_type = issue['issue_type']
        if issue_type not in issues_by_type:
            issues_by_type[issue_type] = []
        issues_by_type[issue_type].append(issue)
    
    # Add each issue type
    for issue_type, issues in issues_by_type.items():
        report += f"### {issue_type} ({len(issues)})\n\n"
        
        if issue_type == 'Far from state centroid':
            report += "| Store | State | Distance from Centroid (km) |\n"
            report += "|-------|-------|---------------------------|\n"
            for issue in issues:
                report += f"| {issue['store']} | {issue['state']} | {issue['centroid_distance_km']:.1f} |\n"
        elif issue_type == 'Multiple stores with identical coordinates':
            for issue in issues:
                report += f"- **Coordinates**: {issue['coords'][0]:.6f}, {issue['coords'][1]:.6f}\n"
                report += f"  - **Number of stores**: {issue['count']}\n"
                report += "  - **Stores**:\n"
                for store in issue['stores']:
                    report += f"    - {store}\n"
                report += "\n"
        else:
            # Generic format for other issue types
            for issue in issues:
                report += f"- {str(issue)}\n"
        
        report += "\n"
    
    # Add cache statistics if available
    if 'cache_stats' in analysis_results:
        cache_stats = analysis_results['cache_stats']
        report += """## Cache Statistics

- **Total Cached Addresses**: {0}
- **Failed Cache Entries**: {1}
- **Cache Failure Rate**: {2:.1f}%

""".format(
            cache_stats['total_cached_addresses'],
            cache_stats['failed_cache_entries'],
            cache_stats['cache_failure_rate']
        )
    
    # Add recommendations
    report += """## Recommendations

Based on the analysis, here are recommendations for improving geocoding quality:

1. **Address Data Quality**: Ensure complete address information including street, number, colony, municipality, state, and postal code.

2. **State Verification**: For states with poor geocoding performance, verify the address data manually.

3. **Review Flagged Issues**: Investigate stores flagged with potential issues, particularly those with identical coordinates.

4. **Geocoding Service**: Consider using alternative geocoding services for areas with poor success rates.

5. **Cache Maintenance**: Periodically review and clean the geocoding cache to remove incorrect entries.
"""
    
    # Save the report
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"Geocoding report saved to {output_file}")

def main():
    """
    Main function to run the geocoding validation tool from command line
    """
    parser = argparse.ArgumentParser(description='Validate geocoding results for store data')
    parser.add_argument('data_file', type=str, help='Path to the geocoded data file (CSV)')
    parser.add_argument('--cache', type=str, help='Path to geocoding cache file (JSON)')
    parser.add_argument('--output-map', type=str, default='geocoding_validation.html', 
                       help='Path to save the validation map (HTML)')
    parser.add_argument('--output-report', type=str, default='geocoding_report.md',
                       help='Path to save the validation report (Markdown)')
    parser.add_argument('--distance-threshold', type=float, default=10.0,
                       help='Threshold in kilometers for detecting potential issues')
    
    args = parser.parse_args()
    
    # Load the data
    df = pd.read_csv(args.data_file)
    
    # Analyze geocoding results
    results = analyze_geocoding_results(df, args.cache, args.distance_threshold)
    
    # Create validation map
    create_validation_map(df, results, args.output_map)
    
    # Generate report
    generate_report(results, args.output_report)

if __name__ == "__main__":
    main()