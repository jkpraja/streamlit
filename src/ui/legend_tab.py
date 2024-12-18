import streamlit as st
import pandas as pd

def render_sheet_data(sheet_name, sheet_data, sku_manager):
    """
    Render a single sheet's data.
    """
    if sheet_data.empty:
        st.info(f"No data found in sheet: {sheet_name}")
        return
    
    # Create column configuration based on actual columns
    column_config = {}
    for col in sheet_data.columns:
        # Configure each column with appropriate width
        column_config[col] = st.column_config.TextColumn(
            col,
            width="medium" if len(str(col)) < 15 else "large"
        )
    
    # Display the sheet data with column configuration
    st.dataframe(
        sheet_data,
        column_config=column_config,
        hide_index=True,
        use_container_width=True
    )
    
    # Show column information
    with st.expander("Sheet Information"):
        st.write(f"Number of columns: {len(sheet_data.columns)}")
        st.write("Columns:")
        for col in sheet_data.columns:
            st.write(f"- {col}")

def render_legend_tab(sku_manager):
    """
    Render the Legend tab with all available sheets from the spreadsheet.
    """
    st.header("Legend")
    
    # Get available sheets
    sheets = sku_manager.get_available_sheets()
    
    if not sheets:
        st.error("No sheets found in the legend spreadsheet")
        st.info("""
            Please ensure the legend spreadsheet exists in:
            legend/legend.xlsx
            
            Add sheets to the spreadsheet to view them here.
        """)
        return
    
    # Create tabs for each sheet
    tabs = st.tabs(sheets)
    
    # Render each sheet's data in its tab
    for tab, sheet_name in zip(tabs, sheets):
        with tab:
            sheet_data = sku_manager.get_sheet_data(sheet_name)
            render_sheet_data(sheet_name, sheet_data, sku_manager)
    
    # Add help text at the bottom
    st.markdown("---")
    st.markdown("""
        ### Legend Spreadsheet Guide
        1. The spreadsheet is located in `legend/legend.xlsx`
        2. Each sheet is displayed in a separate tab above
        3. Only columns with data are displayed
        4. Use the Sheet Information expander to see column details
    """)
