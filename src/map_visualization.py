import folium
import json
import pandas as pd
import os
from folium import plugins

def inspect_geojson(geojson_path):
    """
    Inspect the structure of a GeoJSON file and print available properties
    
    Parameters:
    -----------
    geojson_path : str
        Path to GeoJSON file
    """
    try:
        with open(geojson_path, encoding='utf-8') as f:
            data = json.load(f)
        
        print("GeoJSON Structure Analysis:")
        print(f"Type: {data.get('type', 'Unknown')}")
        
        features = data.get('features', [])
        print(f"Number of features: {len(features)}")
        
        if features:
            # Look at the first feature's properties
            first_feature = features[0]
            properties = first_feature.get('properties', {})
            print("\nAvailable properties:")
            for prop_name, prop_value in properties.items():
                print(f"  - {prop_name}: {type(prop_value).__name__} (Example: {prop_value})")
            
            return properties.keys()
    except Exception as e:
        print(f"Error inspecting GeoJSON: {e}")
        return []

def style_state_by_performance(feature, state_summary, metric='var_ventas'):
    """
    Style function for GeoJSON state polygons based on performance metric
    
    Parameters:
    -----------
    feature : dict
        GeoJSON feature
    state_summary : pd.DataFrame
        DataFrame with state performance summaries
    metric : str
        Metric to use for coloring (default: 'var_ventas')
        
    Returns:
    --------
    dict
        Style dictionary for the feature
    """
    # Try to get the state name from the feature
    state_name = None
    if feature.get('properties'):
        # Try different possible property names for state
        for prop_name in ['sta_name', 'name', 'NAME_1', 'NAME', 'state', 'Estado']:
            if prop_name in feature['properties']:
                state_name = feature['properties'][prop_name]
                break
    
    if not state_name:
        return {
            'fillColor': '#D3D3D3',  # Light gray
            'color': '#000000',      # Black outline
            'weight': 1,
            'fillOpacity': 0.5
        }
    
    # Clean state name for comparison (capitalized)
    state_name = state_name.strip().title()
    
    # Find the state in our summary data
    state_data = None
    for idx, row in state_summary.iterrows():
        row_state = str(row.get('estado', '')).strip().title()
        if row_state == state_name:
            state_data = row
            break
    
    # Alternative: Try matching by prefix
    if state_data is None:
        for idx, row in state_summary.iterrows():
            row_state = str(row.get('estado', '')).strip().title()
            if state_name.startswith(row_state) or row_state.startswith(state_name):
                state_data = row
                break
    
    # If still not found, use default
    if state_data is None:
        return {
            'fillColor': '#D3D3D3',  # Light gray
            'color': '#000000',      # Black outline
            'weight': 1,
            'fillOpacity': 0.5
        }
    
    # Get the performance value
    value = state_data.get(metric)
    
    # Determine color based on performance
    if value is None:
        color = '#D3D3D3'  # Light gray for no data
    elif value < -10:
        color = '#FF0000'  # Red for significant decrease
    elif value < 0:
        color = '#FF8C00'  # Dark orange for slight decrease
    elif value < 5:
        color = '#FFFF00'  # Yellow for neutral/slight increase
    elif value < 20:
        color = '#90EE90'  # Light green for good increase
    else:
        color = '#008000'  # Dark green for excellent increase
    
    return {
        'fillColor': color,
        'color': '#000000',  # Black outline
        'weight': 1,
        'fillOpacity': 0.7   # More opaque to show colors better
    }

def format_percentage(value):
    """Helper function to format percentage values safely"""
    if pd.notna(value):
        return f"{value:.1f}%"
    else:
        return "N/A"

def create_monthly_map(df, state_summary, estados_geo, month):
    """
    Create a map for a specific month
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with store data for this month
    state_summary : pd.DataFrame
        Summary of state performances
    estados_geo : dict
        GeoJSON data for Mexican states
    month : str
        Month name
        
    Returns:
    --------
    folium.Map
        Folium map object
    """
    # Create the base map
    m = folium.Map(location=[23.6345, -102.5528], zoom_start=5, 
                  tiles='cartodbpositron')
    
    # Add title
    title_html = f'''
        <h3 align="center" style="font-size:16px"><b>Desempeño de Tiendas - {month} 2025</b></h3>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Add GeoJSON with state coloring based on performance
    folium.GeoJson(
        estados_geo,
        name=f'Estados - {month}',
        style_function=lambda feature: style_state_by_performance(feature, state_summary, metric='var_ventas')
    ).add_to(m)
    
    # Add marker clusters for stores
    marker_cluster = plugins.MarkerCluster(name='Tiendas').add_to(m)
    
    # Add markers for each store
    for idx, row in df.iterrows():
        if pd.notna(row.get('latitud')) and pd.notna(row.get('longitud')):
            # Determine marker color based on sales variation
            if 'var_ventas' in row and pd.notna(row['var_ventas']):
                if row['var_ventas'] < -10:
                    color = 'red'
                elif row['var_ventas'] < 0:
                    color = 'orange'
                elif row['var_ventas'] < 5:
                    color = 'beige'
                elif row['var_ventas'] < 20:
                    color = 'lightgreen'
                else:
                    color = 'darkgreen'
            else:
                color = 'blue'
            
            # Create popup content with safe formatting
            ventas_str = format_percentage(row.get('var_ventas'))
            ov_str = format_percentage(row.get('var_ov'))
            ticket_str = format_percentage(row.get('var_ticket'))
            
            popup_content = f"""
            <div style='min-width: 180px'>
                <b>{row['Sucursal']}</b><br>
                <b>Formato:</b> {row.get('Formato', 'N/A')}<br>
                <b>Zona:</b> {row.get('Zona', 'N/A')}<br>
                <b>Distrito:</b> {row.get('Distrito', 'N/A')}<br>
                <hr style='margin: 5px 0'>
                <b>Variación Ventas:</b> {ventas_str}<br>
                <b>Variación OV:</b> {ov_str}<br>
                <b>Variación Ticket:</b> {ticket_str}
            </div>
            """
            
            folium.Marker(
                location=[row['latitud'], row['longitud']],
                popup=folium.Popup(popup_content, max_width=300),
                tooltip=row['Sucursal'],
                icon=folium.Icon(color=color, icon='info-sign', prefix='glyphicon')
            ).add_to(marker_cluster)
    
    # Add Layer Control
    folium.LayerControl().add_to(m)
    
    # Add top performers box
    if 'var_ventas' in df.columns:
        top_performers = df.sort_values(by='var_ventas', ascending=False).head(5)
        top_performers_html = f"""
        <div style="position: fixed; 
                    bottom: 50px; 
                    right: 50px; 
                    width: 200px; 
                    height: auto; 
                    padding: 10px; 
                    background-color: white; 
                    border-radius: 5px; 
                    box-shadow: 0 0 15px rgba(0,0,0,0.2); 
                    z-index: 1000;">
            <h4 style="margin-top: 0;">Top 5 Tiendas</h4>
            <ol style="padding-left: 20px; margin-bottom: 0;">
        """
        
        for i, (_, row) in enumerate(top_performers.iterrows()):
            value_str = format_percentage(row.get('var_ventas'))
            top_performers_html += f"<li>{row['Sucursal']}: {value_str}</li>"
        
        top_performers_html += """
            </ol>
        </div>
        """
        
        m.get_root().html.add_child(folium.Element(top_performers_html))
    
    return m

def create_combined_map(combined_df, state_summary, estados_geo):
    """
    Create a combined map with all months' data
    
    Parameters:
    -----------
    combined_df : pd.DataFrame
        Combined DataFrame with all months
    state_summary : pd.DataFrame
        Summary of state performances by month
    estados_geo : dict
        GeoJSON data for Mexican states
        
    Returns:
    --------
    folium.Map
        Combined map
    """
    # Create base map
    m = folium.Map(location=[23.6345, -102.5528], zoom_start=5, 
                   tiles='cartodbpositron')
    
    # Add title
    title_html = f'''
        <h3 align="center" style="font-size:16px"><b>Desempeño de Tiendas 2025 - Vista Combinada</b></h3>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Create a summary of all data across months
    if state_summary is not None:
        if 'month' in state_summary.columns:
            # Group by estado, ignoring month
            all_months_state_summary = state_summary.groupby('estado')[['var_ventas', 'var_ov', 'var_ticket']].mean().reset_index()
        else:
            all_months_state_summary = state_summary
    else:
        # If no summary provided, create one from combined data
        if 'Estado' in combined_df.columns:
            all_months_state_summary = combined_df.groupby('Estado')[['var_ventas', 'var_ov', 'var_ticket']].mean().reset_index()
            all_months_state_summary = all_months_state_summary.rename(columns={'Estado': 'estado'})
        else:
            all_months_state_summary = combined_df.groupby('estado')[['var_ventas', 'var_ov', 'var_ticket']].mean().reset_index()
    
    # Add GeoJSON with state coloring based on performance
    folium.GeoJson(
        estados_geo,
        name='Estados',
        style_function=lambda feature: style_state_by_performance(feature, all_months_state_summary, metric='var_ventas')
    ).add_to(m)
    
    # Get available months
    months = combined_df['month'].unique()
    
    # Create a marker cluster group for each month
    for i, month in enumerate(months):
        # Filter data for this month
        month_df = combined_df[combined_df['month'] == month]
        
        # Create marker cluster for this month
        marker_cluster = plugins.MarkerCluster(
            name=f'Tiendas - {month}',
            show=(i == 0)  # Show only the first month by default
        ).add_to(m)
        
        # Add markers for each store
        for idx, row in month_df.iterrows():
            if pd.notna(row.get('latitud')) and pd.notna(row.get('longitud')):
                # Determine marker color based on sales variation
                if 'var_ventas' in row and pd.notna(row['var_ventas']):
                    if row['var_ventas'] < -10:
                        color = 'red'
                    elif row['var_ventas'] < 0:
                        color = 'orange'
                    elif row['var_ventas'] < 5:
                        color = 'beige'
                    elif row['var_ventas'] < 20:
                        color = 'lightgreen'
                    else:
                        color = 'darkgreen'
                else:
                    color = 'blue'
                
                # Create popup content with safe formatting
                ventas_str = format_percentage(row.get('var_ventas'))
                ov_str = format_percentage(row.get('var_ov'))
                ticket_str = format_percentage(row.get('var_ticket'))
                
                popup_content = f"""
                <div style='min-width: 180px'>
                    <b>{row['Sucursal']}</b><br>
                    <b>Formato:</b> {row.get('Formato', 'N/A')}<br>
                    <b>Zona:</b> {row.get('Zona', 'N/A')}<br>
                    <b>Distrito:</b> {row.get('Distrito', 'N/A')}<br>
                    <hr style='margin: 5px 0'>
                    <b>Variación Ventas:</b> {ventas_str}<br>
                    <b>Variación OV:</b> {ov_str}<br>
                    <b>Variación Ticket:</b> {ticket_str}
                </div>
                """
                
                folium.Marker(
                    location=[row['latitud'], row['longitud']],
                    popup=folium.Popup(popup_content, max_width=300),
                    tooltip=row['Sucursal'],
                    icon=folium.Icon(color=color, icon='info-sign', prefix='glyphicon')
                ).add_to(marker_cluster)
    
    # Add Layer Control
    folium.LayerControl().add_to(m)
    
    # Add instructions box
    instructions_html = """
    <div style="position: fixed; 
                bottom: 50px; 
                right: 50px; 
                width: 220px; 
                height: auto; 
                padding: 10px; 
                background-color: white; 
                border-radius: 5px; 
                box-shadow: 0 0 15px rgba(0,0,0,0.2); 
                z-index: 1000;">
        <h4 style="margin-top: 0;">Instrucciones</h4>
        <p style="margin-bottom: 0;">
            Use el control de capas en la esquina superior derecha para alternar entre los diferentes meses.
        </p>
    </div>
    """
    
    m.get_root().html.add_child(folium.Element(instructions_html))
    
    return m

def create_dashboard_map(df, month, geojson_path, metric='var_ventas'):
    """
    Create a comprehensive dashboard map with multiple indicators
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with store data
    month : str
        Month name for the title
    geojson_path : str
        Path to the GeoJSON file with state polygons
    metric : str, optional
        Primary metric to use for visualization (default: 'var_ventas')
        
    Returns:
    --------
    folium.Map
        Dashboard map
    """
    # Load GeoJSON data
    try:
        with open(geojson_path, encoding='utf-8') as f:
            estados_geo = json.load(f)
    except Exception as e:
        print(f"Error loading GeoJSON: {e}")
        return None
    
    # Create state summary
    if 'Estado' in df.columns:
        state_summary = df.groupby('Estado')[[metric, 'var_ov', 'var_ticket']].mean().reset_index()
        state_summary = state_summary.rename(columns={'Estado': 'estado'})
    else:
        state_summary = df.groupby('estado')[[metric, 'var_ov', 'var_ticket']].mean().reset_index()
    
    # Create the base map
    m = folium.Map(location=[23.6345, -102.5528], zoom_start=5, 
                   tiles='cartodbpositron')
    
    # Add title
    title_html = f'''
        <h3 align="center" style="font-size:16px"><b>Dashboard de Desempeño - {month} 2025</b></h3>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Add GeoJSON with state coloring based on performance
    folium.GeoJson(
        estados_geo,
        name=f'Estados - {metric}',
        style_function=lambda feature: style_state_by_performance(feature, state_summary, metric=metric)
    ).add_to(m)
    
    # Add marker clusters
    marker_cluster = plugins.MarkerCluster(name='Tiendas').add_to(m)
    
    # Add markers for each store
    for idx, row in df.iterrows():
        if pd.notna(row.get('latitud')) and pd.notna(row.get('longitud')):
            # Determine marker color based on metric variation
            if metric in row and pd.notna(row[metric]):
                if row[metric] < -10:
                    color = 'red'
                elif row[metric] < 0:
                    color = 'orange'
                elif row[metric] < 5:
                    color = 'beige'
                elif row[metric] < 20:
                    color = 'lightgreen'
                else:
                    color = 'darkgreen'
            else:
                color = 'blue'
            
            # Create popup content with safe formatting
            ventas_str = format_percentage(row.get('var_ventas'))
            ov_str = format_percentage(row.get('var_ov'))
            ticket_str = format_percentage(row.get('var_ticket'))
            
            popup_content = f"""
            <div style='min-width: 180px'>
                <b>{row['Sucursal']}</b><br>
                <b>Formato:</b> {row.get('Formato', 'N/A')}<br>
                <b>Zona:</b> {row.get('Zona', 'N/A')}<br>
                <b>Distrito:</b> {row.get('Distrito', 'N/A')}<br>
                <hr style='margin: 5px 0'>
                <b>Variación Ventas:</b> {ventas_str}<br>
                <b>Variación OV:</b> {ov_str}<br>
                <b>Variación Ticket:</b> {ticket_str}
            </div>
            """
            
            folium.Marker(
                location=[row['latitud'], row['longitud']],
                popup=folium.Popup(popup_content, max_width=300),
                tooltip=row['Sucursal'],
                icon=folium.Icon(color=color, icon='info-sign', prefix='glyphicon')
            ).add_to(marker_cluster)
    
    # Add Layer Control
    folium.LayerControl().add_to(m)
    
    # Add top and bottom performers box
    if metric in df.columns:
        top_performers = df.sort_values(by=metric, ascending=False).head(5)
        bottom_performers = df.sort_values(by=metric, ascending=True).head(5)
        
        performers_html = f"""
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
            <h4 style="margin-top: 0;">Top 5 Tiendas</h4>
            <ol style="padding-left: 20px; margin-bottom: 10px;">
        """
        
        for i, (_, row) in enumerate(top_performers.iterrows()):
            value_str = format_percentage(row.get(metric))
            performers_html += f"<li>{row['Sucursal']}: {value_str}</li>"
        
        performers_html += """
            </ol>
            <h4 style="margin-top: 10px;">Bottom 5 Tiendas</h4>
            <ol style="padding-left: 20px; margin-bottom: 0;">
        """
        
        for i, (_, row) in enumerate(bottom_performers.iterrows()):
            value_str = format_percentage(row.get(metric))
            performers_html += f"<li>{row['Sucursal']}: {value_str}</li>"
        
        performers_html += """
            </ol>
        </div>
        """
        
        m.get_root().html.add_child(folium.Element(performers_html))
    
    # Add summary statistics box
    metrics = {
        'var_ventas': 'Variación Ventas',
        'var_ov': 'Variación OV',
        'var_ticket': 'Variación Ticket'
    }
    
    stats_html = """
    <div style="position: fixed; 
                top: 70px; 
                right: 50px; 
                width: 220px; 
                height: auto; 
                padding: 10px; 
                background-color: white; 
                border-radius: 5px; 
                box-shadow: 0 0 15px rgba(0,0,0,0.2); 
                z-index: 1000;">
        <h4 style="margin-top: 0;">Estadísticas Generales</h4>
        <table style="width: 100%;">
    """
    
    for metric_key, metric_name in metrics.items():
        if metric_key in df.columns:
            avg_val = df[metric_key].mean()
            color = "green" if avg_val >= 0 else "red"
            avg_str = format_percentage(avg_val)
            stats_html += f"""
            <tr>
                <td>{metric_name}:</td>
                <td style="text-align: right; color: {color};">{avg_str}</td>
            </tr>
            """
    
    stats_html += """
        </table>
    </div>
    """
    
    m.get_root().html.add_child(folium.Element(stats_html))
    
    return m

def crear_mapa_interactivo(monthly_data, combined_df, geojson_path, output_folder="maps"):
    """
    Create interactive maps for each month and a combined view
    
    Parameters:
    -----------
    monthly_data : dict
        Dictionary with month as key and DataFrame as value
    combined_df : pd.DataFrame
        Combined DataFrame with all months
    geojson_path : str
        Path to the GeoJSON file with state polygons
    output_folder : str, optional
        Folder to save the generated HTML maps (default: "maps")
        
    Returns:
    --------
    dict
        Dictionary with paths to the generated HTML files
    """
    # Ensure output folder exists
    os.makedirs(output_folder, exist_ok=True)
    
    # Load GeoJSON data
    try:
        with open(geojson_path, encoding='utf-8') as f:
            estados_geo = json.load(f)
        print(f"Successfully loaded GeoJSON from {geojson_path}")
        
        # Analyze GeoJSON structure
        if 'features' in estados_geo and len(estados_geo['features']) > 0:
            first_feature = estados_geo['features'][0]
            if 'properties' in first_feature:
                print("GeoJSON properties:", list(first_feature['properties'].keys()))
            else:
                print("Warning: No properties found in GeoJSON features")
    except Exception as e:
        print(f"Error loading GeoJSON: {e}")
        return {}
    
    # Create maps for each month and combined view
    map_paths = {}
    
    # Process each month
    for month, df in monthly_data.items():
        print(f"Creating map for {month}...")
        # Create state summary for this month
        if 'Estado' in df.columns:
            state_summary = df.groupby('Estado')[['var_ventas', 'var_ov', 'var_ticket']].mean().reset_index()
            state_summary = state_summary.rename(columns={'Estado': 'estado'})
        else:
            state_summary = df.groupby('estado')[['var_ventas', 'var_ov', 'var_ticket']].mean().reset_index()
        
        # Create the map for this month
        try:
            month_map = create_monthly_map(df, state_summary, estados_geo, month)
            
            # Save the map
            map_file = os.path.join(output_folder, f"mapa_{month.lower()}.html")
            month_map.save(map_file)
            map_paths[month] = map_file
            print(f"Map for {month} saved to {map_file}")
        except Exception as e:
            print(f"Error creating map for {month}: {e}")
    
    # Create combined view with all months
    if len(monthly_data) > 1:
        try:
            print("Creating combined map...")
            # Create state summary across all months
            if 'Estado' in combined_df.columns:
                combined_state_summary = combined_df.groupby(['month', 'Estado'])[['var_ventas', 'var_ov', 'var_ticket']].mean().reset_index()
                combined_state_summary = combined_state_summary.rename(columns={'Estado': 'estado'})
            else:
                combined_state_summary = combined_df.groupby(['month', 'estado'])[['var_ventas', 'var_ov', 'var_ticket']].mean().reset_index()
            
            # Create the combined map
            combined_map = create_combined_map(combined_df, combined_state_summary, estados_geo)
            
            # Save the combined map
            combined_map_file = os.path.join(output_folder, "mapa_combined.html")
            combined_map.save(combined_map_file)
            map_paths['Combined'] = combined_map_file
            print(f"Combined map saved to {combined_map_file}")
        except Exception as e:
            print(f"Error creating combined map: {e}")
    
    # Create dashboard maps for each month
    for month, df in monthly_data.items():
        try:
            print(f"Creating dashboard for {month}...")
            dashboard_map = create_dashboard_map(df, month, geojson_path)
            if dashboard_map:
                dashboard_path = os.path.join(output_folder, f"dashboard_{month.lower()}.html")
                dashboard_map.save(dashboard_path)
                map_paths[f"Dashboard_{month}"] = dashboard_path
                print(f"Dashboard map for {month} saved to {dashboard_path}")
        except Exception as e:
            print(f"Error creating dashboard for {month}: {e}")
    
    # Create heatmaps for different metrics
    metrics = ['var_ventas', 'var_ov', 'var_ticket']
    for metric in metrics:
        try:
            print(f"Creating heatmap for {metric}...")
            create_heatmap(combined_df, metric, output_folder)
        except Exception as e:
            print(f"Error creating heatmap for {metric}: {e}")
    
    return map_paths

def create_heatmap(df, metric='var_ventas', output_folder="maps"):
    """
    Create a heatmap of store performance
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with store data
    metric : str, optional
        Metric to use for heatmap intensity (default: 'var_ventas')
    output_folder : str, optional
        Folder to save the generated heatmap (default: "maps")
        
    Returns:
    --------
    str
        Path to the generated heatmap HTML file
    """
    import folium
    from folium import plugins
    import os
    import pandas as pd
    
    # Ensure output folder exists
    os.makedirs(output_folder, exist_ok=True)
    
    # Create base map
    m = folium.Map(location=[23.6345, -102.5528], zoom_start=5, 
                   tiles='cartodbpositron')
    
    # Filter stores with coordinates and valid metric values
    valid_coords = df[
        (pd.notna(df['latitud'])) & 
        (pd.notna(df['longitud'])) &
        (pd.notna(df[metric]))
    ].copy()
    
    # If no valid coordinates, return empty map
    if len(valid_coords) == 0:
        print(f"Warning: No valid coordinates found for heatmap ({metric})")
        heatmap_file = os.path.join(output_folder, f"heatmap_{metric}.html")
        m.save(heatmap_file)
        return heatmap_file
    
    # Use pandas' numeric_only parameter for safety
    metric_min = valid_coords[metric].min()
    metric_max = valid_coords[metric].max()
    metric_range = metric_max - metric_min
    
    # Simple normalization for intensity
    if metric_range > 0:
        # Create safe intensity values (0.0 to 1.0)
        valid_coords.loc[:, 'intensity'] = 0.5  # Default value
        for idx in valid_coords.index:
            try:
                # Safely convert to float and normalize
                val = float(valid_coords.loc[idx, metric])
                normalized = (val - metric_min) / metric_range
                valid_coords.loc[idx, 'intensity'] = normalized
            except (ValueError, TypeError):
                # Keep default if conversion fails
                pass
    else:
        valid_coords.loc[:, 'intensity'] = 0.5  # Default value if all values are the same
    
    # Create heatmap data
    heat_data = []
    for idx, row in valid_coords.iterrows():
        try:
            # Only use values that can be properly converted to float
            lat = float(row['latitud'])
            lon = float(row['longitud'])
            intensity = float(row['intensity'])
            heat_data.append([lat, lon, intensity])
        except (ValueError, TypeError):
            # Skip invalid entries
            continue
    
    # Add heatmap layer
    plugins.HeatMap(heat_data, radius=15, blur=10, gradient={
        0.0: 'blue',
        0.25: 'purple',
        0.5: 'yellow',
        0.75: 'orange',
        1.0: 'red'
    }).add_to(m)
    
    # Add title
    title_html = f'''
        <h3 align="center" style="font-size:16px"><b>Mapa de Calor - {metric}</b></h3>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Save the heatmap
    heatmap_file = os.path.join(output_folder, f"heatmap_{metric}.html")
    m.save(heatmap_file)
    print(f"Heatmap for {metric} saved to {heatmap_file}")
    
    return heatmap_file