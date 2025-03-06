import pandas as pd
import os
import argparse
from tqdm import tqdm

def extract_store_metadata(df, sap_column='Suc SAP'):
    """
    Extract store metadata from SAP code and store name.
    This is useful when migrating from the old data format to the new one.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with store data
    sap_column : str, optional
        Name of column containing SAP codes (default: 'Suc SAP')
        
    Returns:
    --------
    pd.DataFrame
        DataFrame with added metadata columns (best guesses)
    """
    # Create a copy of the input DataFrame
    result_df = df.copy()
    
    # Initialize new columns
    result_df['Zona'] = None
    result_df['Distrito'] = None
    result_df['Ciudad'] = None
    result_df['estado'] = None
    
    # Extract data from store names
    for i, row in tqdm(result_df.iterrows(), total=len(result_df), desc="Extracting metadata"):
        store_name = row['Sucursal']
        
        # Try to extract city/location from store name
        parts = store_name.split(' ')
        if len(parts) > 1:
            # Guess the city - typically the first word(s) before identifiers like "Centro", "Plaza", etc.
            city_words = []
            for word in parts:
                if word.upper() in ['CENTRO', 'PLAZA', 'GALERIAS', 'CHEDRAUI', 'SEARS', 'COPPEL']:
                    break
                city_words.append(word)
            
            if city_words:
                result_df.at[i, 'Ciudad'] = ' '.join(city_words)
        
        # Assign zones based on SAP codes (simplified example - adjust as needed)
        sap_code = row[sap_column]
        if isinstance(sap_code, str):
            if sap_code.startswith('A'):
                result_df.at[i, 'Zona'] = 'Centro'
            elif sap_code.startswith('B'):
                result_df.at[i, 'Zona'] = 'Sur'
            elif sap_code.startswith('C'):
                result_df.at[i, 'Zona'] = 'Norte'
            else:
                result_df.at[i, 'Zona'] = 'Desconocido'
                
            # Assign districts based on numeric part of SAP (simplified)
            if len(sap_code) > 1:
                try:
                    num_part = int(sap_code[1:])
                    if num_part < 500:
                        result_df.at[i, 'Distrito'] = 'Distrito 1'
                    elif num_part < 700:
                        result_df.at[i, 'Distrito'] = 'Distrito 2'
                    elif num_part < 900:
                        result_df.at[i, 'Distrito'] = 'Distrito 3'
                    else:
                        result_df.at[i, 'Distrito'] = 'Distrito 4'
                except:
                    result_df.at[i, 'Distrito'] = 'Desconocido'
    
    return result_df

def migrate_data(old_file, new_template_file, output_file=None):
    """
    Migrate data from old format to new format using a template file.
    
    Parameters:
    -----------
    old_file : str
        Path to old format data file
    new_template_file : str
        Path to a file in the new format (used as template)
    output_file : str, optional
        Path to save the migrated data (default: None, in which case it adds '_migrated' to old filename)
        
    Returns:
    --------
    pd.DataFrame
        Migrated DataFrame
    str
        Path to the saved file
    """
    # Load the old data
    old_df = pd.read_csv(old_file)
    
    # Load the new template for column structure
    template_df = pd.read_csv(new_template_file)
    
    # Create an empty DataFrame with the new structure
    new_df = pd.DataFrame(columns=template_df.columns)
    
    # Copy common columns
    common_columns = set(old_df.columns) & set(new_df.columns)
    for col in common_columns:
        new_df[col] = old_df[col]
    
    # Translate columns with different names
    column_mapping = {
        'Venta Neta MT 2024 vs 2023': '$ Crec% MT 2025 vs 2024',
        'OV MT 2024 vs 2023': 'Ordenes Crec% MT 2025 vs 2024',
        'Ticket MT 2024 vs 2023': 'Ticket Crec% MT 2025 vs 2024'
    }
    
    for old_col, new_col in column_mapping.items():
        if old_col in old_df.columns and new_col in new_df.columns:
            new_df[new_col] = old_df[old_col]
    
    # Extract metadata from store names and SAP codes
    enhanced_df = extract_store_metadata(new_df)
    
    # Save the migrated file
    if output_file is None:
        base, ext = os.path.splitext(old_file)
        output_file = f"{base}_migrated{ext}"
    
    enhanced_df.to_csv(output_file, index=False)
    print(f"Migrated data saved to {output_file}")
    
    return enhanced_df, output_file

def main():
    """
    Main function to run the data migration tool from command line
    """
    parser = argparse.ArgumentParser(description='Migrate store data from old format to new format')
    parser.add_argument('old_file', type=str, help='Path to the old format data file')
    parser.add_argument('template_file', type=str, help='Path to a file in the new format (used as template)')
    parser.add_argument('--output', '-o', type=str, help='Path to save the migrated data')
    
    args = parser.parse_args()
    
    migrate_data(args.old_file, args.template_file, args.output)

if __name__ == "__main__":
    main()