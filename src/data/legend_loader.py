import pandas as pd
import os
import streamlit as st

def initialize_legend_spreadsheet():
    """
    Create the legend spreadsheet if it doesn't exist.
    """
    legend_path = os.path.join('legend', 'legend.xlsx')
    
    if not os.path.exists('legend'):
        os.makedirs('legend')
    
    if not os.path.exists(legend_path):
        # Create empty DataFrame
        df = pd.DataFrame()
        
        # Save empty spreadsheet
        with pd.ExcelWriter(legend_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Sheet1', index=False)

def get_sheet_names():
    """
    Get list of all sheet names in the legend spreadsheet.
    """
    legend_path = os.path.join('legend', 'legend.xlsx')
    
    try:
        # Initialize spreadsheet if it doesn't exist
        initialize_legend_spreadsheet()
        
        # Read Excel file without loading data
        excel_file = pd.ExcelFile(legend_path)
        return excel_file.sheet_names
    except Exception as e:
        return []

@st.cache_data
def load_sheet_data(sheet_name):
    """
    Load data from a specific sheet in the legend spreadsheet.
    Returns DataFrame with the sheet's data.
    """
    legend_path = os.path.join('legend', 'legend.xlsx')
    
    try:
        # Read the specified sheet from the Excel file
        df = pd.read_excel(legend_path, sheet_name=sheet_name)
        
        # Get only non-empty columns
        non_empty_cols = []
        for col in df.columns:
            # Check if column has any non-null and non-empty values
            if df[col].notna().any() and not (df[col].astype(str).str.strip() == '').all():
                non_empty_cols.append(col)
        
        # Keep only non-empty columns
        df = df[non_empty_cols]
        
        # Clean the data
        for col in df.columns:
            if df[col].dtype == object:  # Only clean string columns
                df[col] = df[col].astype(str).str.strip()
        
        # Remove any rows where all fields are empty
        df = df.dropna(how='all')
        
        return df
        
    except Exception as e:
        return pd.DataFrame()

def save_sheet_data(df, sheet_name):
    """
    Save data back to a specific sheet in the spreadsheet.
    """
    legend_path = os.path.join('legend', 'legend.xlsx')
    
    try:
        # Read all existing sheets
        excel_file = pd.ExcelFile(legend_path)
        all_sheets = {name: pd.read_excel(legend_path, sheet_name=name) 
                     for name in excel_file.sheet_names 
                     if name != sheet_name}
        
        # Save all sheets including the updated one
        with pd.ExcelWriter(legend_path, engine='openpyxl') as writer:
            # Save the updated sheet
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Save all other sheets
            for name, sheet_df in all_sheets.items():
                sheet_df.to_excel(writer, sheet_name=name, index=False)
            
        return True
    except Exception as e:
        return False
