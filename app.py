import streamlit as st
import pandas as pd
from datetime import timedelta

# Import our modules
from src.data.loader import load_data, get_year_colors, get_source_files_hash
from src.data.sku_manager import SKUManager
from src.utils.helpers import (
    filter_dataframe,
    get_title_text,
    calculate_metrics,
    calculate_quarterly_metrics,
    format_quarterly_display,
    get_sku_metrics,
    get_month_name,
    get_daily_sales_by_year,
    add_quarter
)
from src.visualizations.charts import (
    create_sku_revenue_chart,
    create_quarterly_chart,
    create_monthly_chart,
    create_daily_chart,
    create_geo_chart
)
from src.ui.components import (
    render_sidebar,
    render_metrics,
    render_quarterly_metrics_table,
    render_sku_metrics_table,
    render_chart
)
from src.ui.legend_tab import render_legend_tab

# Set page config
st.set_page_config(page_title="Amazon FBA Sales Dashboard", layout="wide")

# Initialize SKU manager
sku_manager = SKUManager()

# Get hash of source files to detect changes
source_files_hash = get_source_files_hash()

# Load data with SKU mapping
df = load_data(_sku_manager=sku_manager, _files_hash=source_files_hash)

if df.empty:
    st.warning("No data available. Please check the source directory for CSV files.")
else:
    # Get color scheme for years
    year_colors = get_year_colors(df)
    
    # Create tabs
    tab_dashboard, tab_legend = st.tabs(["Dashboard", "Legend"])
    
    with tab_dashboard:
        # Render sidebar and get filter values
        st.sidebar.markdown("### Filters")
        
        # SKU filter - multiselect
        all_skus = sorted(df['SKU'].unique().tolist())
        selected_skus = st.sidebar.multiselect(
            'Select SKUs',
            options=all_skus,
            default=None,
            placeholder="Select SKUs (empty = all)"
        )
        
        # Calculate relative years for SKU if one is selected
        if len(selected_skus) == 1:
            sku_data = df[df['SKU'] == selected_skus[0]]
            first_sale_date = sku_data['Purchase Date'].min()
            last_sale_date = sku_data['Purchase Date'].max()
            min_date = first_sale_date.date()
            max_date = last_sale_date.date()
            
            # Calculate number of 365-day periods
            total_days = (last_sale_date - first_sale_date).days
            num_periods = total_days // 365 + 1
            
            # Create period options
            relative_year_options = [f"{i}st Year" if i == 1 else f"{i}nd Year" if i == 2 
                                   else f"{i}rd Year" if i == 3 else f"{i}th Year" 
                                   for i in range(1, num_periods + 1)]
            
            # Create period date ranges for filtering
            period_ranges = []
            for i in range(num_periods):
                start = first_sale_date + timedelta(days=i * 365)
                end = min(start + timedelta(days=364), last_sale_date)  # end is inclusive
                period_ranges.append((start, end))
            
            st.sidebar.markdown(f"#### SKU Date Range")
            st.sidebar.markdown(f"First sale: {min_date}")
            st.sidebar.markdown(f"Last sale: {max_date}")
        else:
            min_date = df['Purchase Date'].min().date()
            max_date = df['Purchase Date'].max().date()
            relative_year_options = []
            period_ranges = []
        
        # Date Range filter
        st.sidebar.markdown("#### Date Range")
        start_date = st.sidebar.date_input('Start Date', min_date, min_value=min_date, max_value=max_date)
        end_date = st.sidebar.date_input('End Date', max_date, min_value=min_date, max_value=max_date)
        
        st.sidebar.markdown("#### Quick Filters")
        
        # Relative Year filter (only shown when single SKU is selected)
        if relative_year_options:
            selected_relative_years = st.sidebar.multiselect(
                'Select Relative Years',
                options=relative_year_options,
                default=None,
                placeholder="Select relative years (empty = all)"
            )
        
        # Month filter - multiselect
        months = sorted(df['Month'].dropna().unique().astype(int).tolist())
        month_options = {m: get_month_name(m) for m in months}
        selected_months = st.sidebar.multiselect(
            'Select Months',
            options=months,
            format_func=lambda x: month_options[x],
            default=None,
            placeholder="Select months (empty = all)"
        )

        # Year filter - multiselect
        years = sorted(df['Year'].dropna().unique().astype(int).tolist())
        selected_years = st.sidebar.multiselect(
            'Select Years',
            options=years,
            default=None,
            placeholder="Select years (empty = all)"
        )

        # Location filter - multiselect with state codes from legend
        if 'Shipping State' in df.columns:
            # Get valid states and their names from legend
            valid_states = sku_manager.get_valid_states()
            state_names = sku_manager.get_state_names()
            
            # Use state names in display if available
            selected_states = st.sidebar.multiselect(
                'Select States',
                options=valid_states,
                format_func=lambda x: state_names.get(x, x),
                default=None,
                placeholder="Select states (empty = all)"
            )
        else:
            selected_states = []
        
        # Apply filters
        filtered_df = df.copy()
        
        # Apply date range filter
        filtered_df = filtered_df[
            (filtered_df['Purchase Date'].dt.date >= start_date) &
            (filtered_df['Purchase Date'].dt.date <= end_date)
        ]
        
        # Apply relative year filter if a single SKU is selected
        if len(selected_skus) == 1 and selected_relative_years:
            # Create mask for selected periods
            period_mask = pd.Series(False, index=filtered_df.index)
            for rel_year in selected_relative_years:
                year_num = int(rel_year.split('st' if '1st' in rel_year else 
                                           'nd' if '2nd' in rel_year else 
                                           'rd' if '3rd' in rel_year else 
                                           'th')[0])
                period_start, period_end = period_ranges[year_num - 1]
                period_mask |= (
                    (filtered_df['Purchase Date'] >= period_start) &
                    (filtered_df['Purchase Date'] <= period_end)
                )
            filtered_df = filtered_df[period_mask]
        
        if selected_skus:
            filtered_df = filtered_df[filtered_df['SKU'].isin(selected_skus)]
        if selected_months:
            filtered_df = filtered_df[filtered_df['Month'].isin(selected_months)]
        if selected_years:
            filtered_df = filtered_df[filtered_df['Year'].isin(selected_years)]
        if selected_states and 'Shipping State' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['Shipping State'].isin(selected_states)]
        
        # Dashboard title
        st.title("Amazon FBA Sales Dashboard")
        
        # Custom title based on selections
        title_parts = []
        if start_date != min_date or end_date != max_date:
            title_parts.append(f"Date Range: {start_date} to {end_date}")
        if len(selected_skus) == 1 and selected_relative_years:
            title_parts.append(f"Relative Years: {', '.join(selected_relative_years)}")
        if selected_years:
            title_parts.append(f"Years: {', '.join(map(str, selected_years))}")
        if selected_months:
            month_names = [month_options[m] for m in selected_months]
            title_parts.append(f"Months: {', '.join(month_names)}")
        if not title_parts:
            title_parts.append("All Time")
        st.markdown(f"### Sales Analysis - {' | '.join(title_parts)}")
        
        # Render top-level metrics
        render_metrics(calculate_metrics(filtered_df))
        
        # Sales Analysis Section
        st.markdown("### Sales Analysis")
        if len(selected_skus) == 1:
            # Show monthly revenue for single selected SKU using filtered data
            monthly_data = filtered_df.groupby(['Year', 'Month', 'Month_Name']).agg({
                'Revenue': 'sum',
                'Shipped Quantity': 'sum'
            }).reset_index()
            
            # Sort by Year and Month
            monthly_data = monthly_data.sort_values(['Year', 'Month'])
            monthly_data['Period'] = monthly_data['Month_Name'] + ' ' + monthly_data['Year'].astype(str)
            
            # Create and render single SKU chart
            fig_products = create_sku_revenue_chart(monthly_data, None, year_colors)
            render_chart(fig_products)
            
            # Display first and last sale dates
            st.markdown(f"**First sale:** {min_date}")
            st.markdown(f"**Last sale:** {max_date}")
            
            # Display period ranges if relative years are selected
            if selected_relative_years:
                st.markdown("### Selected Period Ranges")
                for rel_year in selected_relative_years:
                    year_num = int(rel_year.split('st' if '1st' in rel_year else 
                                               'nd' if '2nd' in rel_year else 
                                               'rd' if '3rd' in rel_year else 
                                               'th')[0])
                    period_start, period_end = period_ranges[year_num - 1]
                    st.markdown(f"**{rel_year}:** {period_start.date()} to {period_end.date()} (365 days)")
        else:
            # Show revenue by SKU with yearly trends
            sku_sales = filtered_df.groupby(['SKU', 'Year']).agg({
                'Revenue': 'sum',
                'Shipped Quantity': 'sum'
            }).reset_index()
            
            # Sort SKUs by total revenue
            sku_totals = sku_sales.groupby('SKU')['Revenue'].sum().sort_values(ascending=False)
            sorted_skus = sku_totals.index.tolist()
            
            # Create and render SKU comparison chart
            fig_products = create_sku_revenue_chart(sku_sales, sorted_skus, year_colors)
            render_chart(fig_products)
        
        # Quarterly Performance Details
        if not selected_months:  # Only show quarterly analysis when not filtering by specific months
            st.markdown("### Quarterly Performance Details")
            
            # Calculate and prepare quarterly metrics
            quarterly_metrics = calculate_quarterly_metrics(filtered_df, by_sku=bool(selected_skus))
            
            # Create and render quarterly performance chart
            fig_quarterly = create_quarterly_chart(quarterly_metrics, year_colors, show_by_sku=bool(selected_skus))
            render_chart(fig_quarterly)
            
            # Display quarterly metrics table
            quarterly_display = format_quarterly_display(quarterly_metrics)
            render_quarterly_metrics_table(quarterly_display)
        
            # Monthly Breakdown
            st.markdown("### Monthly Breakdown")
            if selected_skus:
                # Group by SKU for selected SKUs
                monthly_breakdown = filtered_df.groupby(['SKU', 'Year', 'Month_Name', 'Month']).agg({
                    'Revenue': 'sum',
                    'Shipped Quantity': 'sum'
                }).reset_index()
            else:
                # Original aggregation for all SKUs
                monthly_breakdown = filtered_df.groupby(['Year', 'Month_Name', 'Month']).agg({
                    'Revenue': 'sum',
                    'Shipped Quantity': 'sum'
                }).reset_index()
            
            # Sort by month number
            monthly_breakdown = monthly_breakdown.sort_values(['Year', 'Month'])
            
            # Create and render monthly breakdown chart
            fig_monthly = create_monthly_chart(monthly_breakdown, year_colors, show_by_sku=bool(selected_skus))
            render_chart(fig_monthly)
        
        # Sales Over Time
        st.markdown("### Daily Sales Trend")
        daily_sales_by_year = get_daily_sales_by_year(filtered_df)
        
        # Create and render daily sales chart with year colors
        fig_trend = create_daily_chart(daily_sales_by_year, year_colors)
        render_chart(fig_trend)
        
        # Geographic Analysis
        if 'Shipping State' in filtered_df.columns:
            st.markdown("### Geographic Distribution")
            state_sales = filtered_df.groupby('Shipping State').agg({
                'Revenue': 'sum',
                'Shipped Quantity': 'sum'
            }).reset_index()
            
            # Create and render geographic distribution chart
            fig_map = create_geo_chart(state_sales)
            render_chart(fig_map)
        
        # SKU Performance Metrics
        st.markdown("### SKU Performance Details")
        sku_metrics = get_sku_metrics(filtered_df)
        render_sku_metrics_table(sku_metrics)
    
    with tab_legend:
        # Render the Legend tab with spreadsheet data
        render_legend_tab(sku_manager)
