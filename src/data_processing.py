import pandas as pd
import os
import json

def read_and_clean_data(file_path):
    """
    Read and clean data from CSV files with robust handling of different number formats.
    
    Parameters:
    -----------
    file_path : str
        Path to the CSV file
        
    Returns:
    --------
    pd.DataFrame
        Cleaned DataFrame with standardized column names
    """
    # Read the CSV file
    import pandas as pd
    import re
    import os
    
    df = pd.read_csv(file_path)
    
    # Identify and standardize column names
    # The new format has columns like '$ Crec% MT 2025 vs 2024' instead of 'Venta Neta MT 2024 vs 2023'
    sales_col = [col for col in df.columns if '$ Crec%' in col or 'Venta Neta' in col][0] if any('$ Crec%' in col or 'Venta Neta' in col for col in df.columns) else None
    orders_col = [col for col in df.columns if 'Ordenes Crec%' in col or 'OV MT' in col][0] if any('Ordenes Crec%' in col or 'OV MT' in col for col in df.columns) else None
    ticket_col = [col for col in df.columns if 'Ticket Crec%' in col or 'Ticket MT' in col][0] if any('Ticket Crec%' in col or 'Ticket MT' in col for col in df.columns) else None
    
    # Create a mapping dictionary for renaming
    rename_dict = {}
    if sales_col:
        rename_dict[sales_col] = 'var_ventas'
    if orders_col:
        rename_dict[orders_col] = 'var_ov'
    if ticket_col:
        rename_dict[ticket_col] = 'var_ticket'
    
    # Rename columns
    df = df.rename(columns=rename_dict)
    
    # Extract month/year from filename for tracking
    filename = os.path.basename(file_path)
    if 'Ene' in filename:
        month = 'Enero'
    elif 'Feb' in filename:
        month = 'Febrero'
    elif 'Mar' in filename:
        month = 'Marzo'
    elif 'Abr' in filename:
        month = 'Abril'
    elif 'May' in filename:
        month = 'Mayo'
    elif 'Jun' in filename:
        month = 'Junio'
    elif 'Jul' in filename:
        month = 'Julio'
    elif 'Ago' in filename:
        month = 'Agosto'
    elif 'Sep' in filename:
        month = 'Septiembre'
    elif 'Oct' in filename:
        month = 'Octubre'
    elif 'Nov' in filename:
        month = 'Noviembre'
    elif 'Dic' in filename:
        month = 'Diciembre'
    else:
        month = 'Unknown'
    
    # Add month column
    df['month'] = month
    
    # Function to safely convert values to float
    def safe_float_convert(value):
        if pd.isna(value):
            return None
        
        if isinstance(value, (int, float)):
            return float(value)
            
        # Convert string to value we can process
        value_str = str(value).strip()
        
        # Check if it's a percentage and remove % sign
        if value_str.endswith('%'):
            value_str = value_str[:-1].strip()
        
        # Replace comma with dot for decimal separator
        value_str = value_str.replace(',', '.')
        
        # Try to convert to float
        try:
            return float(value_str)
        except ValueError:
            # Additional cleanup for complex formats
            # Remove any non-numeric chars except for the decimal point and minus sign
            clean_val = re.sub(r'[^\d.-]', '', value_str)
            try:
                return float(clean_val)
            except ValueError:
                print(f"Warning: Could not convert value '{value}' to float")
                return None
    
    # Convert percentage strings to float values
    for col in ['var_ventas', 'var_ov', 'var_ticket']:
        if col in df.columns:
            df[col] = df[col].apply(safe_float_convert)
    
    return df

def load_multiple_months(data_folder):
    """
    Load and combine data from multiple monthly CSV files
    
    Parameters:
    -----------
    data_folder : str
        Path to the folder containing CSV files
        
    Returns:
    --------
    dict
        Dictionary with month as key and DataFrame as value
    pd.DataFrame
        Combined DataFrame with a 'month' column
    """
    # Dictionary to store DataFrames by month
    monthly_data = {}
    
    # Combined DataFrame
    combined_df = pd.DataFrame()
    
    # Get all CSV files in the data folder
    csv_files = [f for f in os.listdir(data_folder) if f.endswith('.csv') and f.startswith('datos')]
    
    for file in csv_files:
        file_path = os.path.join(data_folder, file)
        df = read_and_clean_data(file_path)
        
        # Store in dictionary by month
        month = df['month'].iloc[0]
        monthly_data[month] = df
        
        # Append to combined DataFrame
        combined_df = pd.concat([combined_df, df], ignore_index=True)
    
    return monthly_data, combined_df

def resumen_por_estado(df, metric='var_ventas'):
    """
    Group data by state and calculate average performance metrics
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with store data
    metric : str, optional
        Metric to use for grouping (default: 'var_ventas')
        
    Returns:
    --------
    pd.DataFrame
        Summary DataFrame grouped by state
    """
    # Check if Estado column exists
    if 'Estado' in df.columns:
        # Use the Estado column directly
        resumen = df.groupby('Estado')[[metric, 'var_ov', 'var_ticket']].mean().reset_index()
        resumen = resumen.rename(columns={'Estado': 'estado'})
    else:
        # Fallback to the old method
        resumen = df.groupby('estado')[[metric, 'var_ov', 'var_ticket']].mean().reset_index()
    
    return resumen

def categorize_performance(value):
    """
    Categorize performance values into predefined ranges
    
    Parameters:
    -----------
    value : float
        Performance value (percentage)
        
    Returns:
    --------
    str
        Category name ('Muy Bajo', 'Bajo', 'Neutral', 'Alto', 'Muy Alto')
    str
        Color code for the category
    """
    if value < -10:
        return 'Muy Bajo', '#FF0000'  # Red
    elif value < 0:
        return 'Bajo', '#FFA500'  # Orange
    elif value < 5:
        return 'Neutral', '#FFFF00'  # Yellow
    elif value < 20:
        return 'Alto', '#90EE90'  # Light Green
    else:
        return 'Muy Alto', '#008000'  # Dark Green

def add_performance_categories(df):
    """
    Add performance categories and colors to the DataFrame
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with performance metrics
        
    Returns:
    --------
    pd.DataFrame
        DataFrame with added category and color columns
    """
    # Add categories and colors for each metric
    for metric in ['var_ventas', 'var_ov', 'var_ticket']:
        if metric in df.columns:
            cat_col = f'{metric}_category'
            color_col = f'{metric}_color'
            
            categories = []
            colors = []
            
            for val in df[metric]:
                cat, color = categorize_performance(val)
                categories.append(cat)
                colors.append(color)
            
            df[cat_col] = categories
            df[color_col] = colors
    
    return df

def get_top_performers(df, metric='var_ventas', n=5, by_state=True):
    """
    Get top performing states or stores
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with performance data
    metric : str, optional
        Metric to rank by (default: 'var_ventas')
    n : int, optional
        Number of top performers to return (default: 5)
    by_state : bool, optional
        If True, group by state; otherwise, use individual stores (default: True)
        
    Returns:
    --------
    pd.DataFrame
        Top n performers
    """
    if by_state:
        if 'Estado' in df.columns:
            grouped = df.groupby('Estado')[metric].mean().reset_index()
            grouped = grouped.sort_values(by=metric, ascending=False)
            return grouped.head(n)
        else:
            grouped = df.groupby('estado')[metric].mean().reset_index()
            grouped = grouped.sort_values(by=metric, ascending=False)
            return grouped.head(n)
    else:
        # For stores, include Sucursal and other relevant columns
        sorted_df = df.sort_values(by=metric, ascending=False)
        return sorted_df[['Sucursal', 'Formato', 'Estado', metric]].head(n)

def get_bottom_performers(df, metric='var_ventas', n=5, by_state=True):
    """
    Get bottom performing states or stores
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with performance data
    metric : str, optional
        Metric to rank by (default: 'var_ventas')
    n : int, optional
        Number of bottom performers to return (default: 5)
    by_state : bool, optional
        If True, group by state; otherwise, use individual stores (default: True)
        
    Returns:
    --------
    pd.DataFrame
        Bottom n performers
    """
    if by_state:
        if 'Estado' in df.columns:
            grouped = df.groupby('Estado')[metric].mean().reset_index()
            grouped = grouped.sort_values(by=metric, ascending=True)
            return grouped.head(n)
        else:
            grouped = df.groupby('estado')[metric].mean().reset_index()
            grouped = grouped.sort_values(by=metric, ascending=True)
            return grouped.head(n)
    else:
        # For stores, include Sucursal and other relevant columns
        sorted_df = df.sort_values(by=metric, ascending=True)
        return sorted_df[['Sucursal', 'Formato', 'Estado', metric]].head(n)

def calculate_month_over_month_growth(monthly_data, metric='var_ventas'):
    """
    Calculate month-over-month growth for states or stores
    
    Parameters:
    -----------
    monthly_data : dict
        Dictionary with month as key and DataFrame as value
    metric : str, optional
        Metric to analyze (default: 'var_ventas')
        
    Returns:
    --------
    pd.DataFrame
        DataFrame with month-over-month growth by state or store
    """
    # Get ordered list of months
    month_order = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                   'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    
    # Filter available months and sort them
    available_months = list(monthly_data.keys())
    available_months.sort(key=lambda m: month_order.index(m) if m in month_order else 999)
    
    if len(available_months) < 2:
        return pd.DataFrame()  # Not enough data for comparison
    
    # Get state averages for each month
    state_avgs = {}
    for month in available_months:
        df = monthly_data[month]
        if 'Estado' in df.columns:
            state_avg = df.groupby('Estado')[metric].mean()
        else:
            state_avg = df.groupby('estado')[metric].mean()
        state_avgs[month] = state_avg
    
    # Calculate month-over-month changes
    mom_changes = {}
    for i in range(1, len(available_months)):
        prev_month = available_months[i-1]
        curr_month = available_months[i]
        
        prev_data = state_avgs[prev_month]
        curr_data = state_avgs[curr_month]
        
        # Get common states
        common_states = set(prev_data.index) & set(curr_data.index)
        
        changes = {}
        for state in common_states:
            # Calculate change in performance metric from previous to current month
            # Note: These are already percentage differences, so we calculate the absolute change in percentage points
            changes[state] = curr_data[state] - prev_data[state]
        
        mom_changes[f'{prev_month} to {curr_month}'] = changes
    
    # Convert to DataFrame
    result_dfs = []
    for period, changes in mom_changes.items():
        df = pd.DataFrame(list(changes.items()), columns=['Estado', 'Change'])
        df['Period'] = period
        result_dfs.append(df)
    
    if result_dfs:
        return pd.concat(result_dfs, ignore_index=True)
    else:
        return pd.DataFrame()