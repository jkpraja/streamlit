import streamlit as st
import pandas as pd
import glob
import os
import hashlib

def get_source_files_hash():
    """
    Generate a hash of all files in the source directory to detect changes.
    """
    hash_md5 = hashlib.md5()
    
    if not os.path.exists('source'):
        return None
        
    # Get all CSV files and sort them for consistent ordering
    csv_files = sorted(glob.glob('source/*.csv'))
    
    for file_path in csv_files:
        try:
            # Update hash with file modification time and size
            stats = os.stat(file_path)
            hash_md5.update(f"{file_path}:{stats.st_mtime}:{stats.st_size}".encode())
        except Exception:
            continue
            
    return hash_md5.hexdigest()

@st.cache_data(ttl=None, show_spinner=False)
def load_data(_sku_manager=None, _files_hash=None):
    """
    Load and process data from CSV files in the source directory.
    Returns processed DataFrame with sales data.
    
    Args:
        _sku_manager: SKU manager instance (underscore prefix to prevent Streamlit hashing)
        _files_hash: Hash of source files (underscore prefix to prevent Streamlit hashing)
    """
    # Get all CSV files in the source directory
    csv_files = glob.glob('source/*.csv')
    
    # Create empty list to store dataframes
    dfs = []
    
    # Read each CSV file and append to list
    for file in csv_files:
        try:
            # Read CSV file with explicit data types
            df = pd.read_csv(
                file,
                low_memory=False,
                dtype={
                    'Merchant SKU': str,
                    'Shipping State': str,
                    'Shipping Country Code': str
                }
            )
            
            # Convert Purchase Date to datetime with UTC
            df['Purchase Date'] = pd.to_datetime(df['Purchase Date'], utc=True)
            
            # Only keep rows where Purchase Date is valid
            df = df[df['Purchase Date'].notna()]
            
            # Clean SKU data
            df['Merchant SKU'] = df['Merchant SKU'].str.strip()
            
            dfs.append(df)
        except Exception as e:
            st.error(f"Error reading file {file}: {str(e)}")
    
    # Combine all dataframes
    if dfs:
        try:
            df = pd.concat(dfs, ignore_index=True)
            
            # Process the combined data
            df['Date'] = df['Purchase Date'].dt.date
            df['Month'] = df['Purchase Date'].dt.month
            df['Month_Name'] = df['Purchase Date'].dt.strftime('%B')
            df['Year'] = df['Purchase Date'].dt.year
            
            # Handle potential NA values in numeric columns
            df['Item Price'] = pd.to_numeric(df['Item Price'], errors='coerce').fillna(0)
            df['Item Promo Discount'] = pd.to_numeric(df['Item Promo Discount'], errors='coerce').fillna(0)
            df['Revenue'] = df['Item Price'] - df['Item Promo Discount']
            df['Shipped Quantity'] = pd.to_numeric(df['Shipped Quantity'], errors='coerce').fillna(0)
            
            # Ensure Month and Year are integers
            df['Month'] = df['Month'].astype('Int64')
            df['Year'] = df['Year'].astype('Int64')
            
            # Drop any rows where critical columns are null
            df = df.dropna(subset=['Year', 'Merchant SKU'])
            
            # Remove any rows where SKU is empty or whitespace
            df = df[df['Merchant SKU'].str.strip() != '']
            
            # Apply SKU mapping if manager is provided
            if _sku_manager is not None:
                df = _sku_manager.map_skus_in_df(df)
            
            return df
        except Exception as e:
            st.error(f"Error processing data: {str(e)}")
            return pd.DataFrame()
    else:
        st.error("No CSV files found in the source directory")
        return pd.DataFrame()

def get_year_colors(df):
    """
    Create a consistent color scheme for years using darker colors.
    Returns a dictionary mapping years to colors.
    """
    dark_colors = [
        '#1f77b4',  # Dark blue
        '#d62728',  # Dark red
        '#2ca02c',  # Dark green
        '#9467bd',  # Dark purple
        '#8c564b',  # Dark brown
        '#e377c2'   # Dark pink
    ]
    all_years = sorted(df['Year'].unique())
    return {year: color for year, color in zip(all_years, dark_colors[:len(all_years)])}
