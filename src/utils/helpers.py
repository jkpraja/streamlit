import calendar
import pandas as pd

def get_month_name(month_num):
    """
    Convert month number to month name, with special handling for 'All' months.
    """
    if month_num == 0:  # 0 represents "All" months
        return "All"
    try:
        return calendar.month_name[int(month_num)]
    except:
        return "Unknown"

def filter_dataframe(df, selected_sku, selected_month, selected_year, selected_state):
    """
    Apply filters to the dataframe based on selected values.
    Note: Now using SKU instead of Merchant SKU for filtering.
    """
    filtered_df = df.copy()
    
    if selected_sku != 'All':
        filtered_df = filtered_df[filtered_df['SKU'] == selected_sku]
    if selected_month != 0:  # Only filter by month if not "All"
        filtered_df = filtered_df[filtered_df['Month'] == selected_month]
    if selected_year != 0:  # Only filter by year if not "All"
        filtered_df = filtered_df[filtered_df['Year'] == selected_year]
    if selected_state != 'All':
        filtered_df = filtered_df[filtered_df['Shipping State'] == selected_state]
    
    return filtered_df

def get_title_text(selected_year, selected_month, get_month_name_func):
    """
    Generate the appropriate title text based on selected filters.
    """
    if selected_year == 0:
        if selected_month == 0:
            return "### Sales Analysis - All Time"
        else:
            return f"### Sales Analysis - {get_month_name_func(selected_month)}, All Years"
    elif selected_month == 0:
        return f"### Sales Analysis - All Months, {selected_year}"
    else:
        return f"### Sales Analysis - {get_month_name_func(selected_month)} {selected_year}"

def calculate_metrics(filtered_df):
    """
    Calculate top-level metrics from the filtered dataframe.
    """
    total_revenue = filtered_df['Revenue'].sum()
    total_orders = len(filtered_df)
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    total_units = filtered_df['Shipped Quantity'].sum()
    
    return {
        'Total Revenue': f"${total_revenue:,.2f}",
        'Total Orders': f"{total_orders:,}",
        'Average Order Value': f"${avg_order_value:.2f}",
        'Units Sold': f"{total_units:,}"
    }

def add_quarter(df):
    """Add quarter column based on month."""
    df = df.copy()
    df['Quarter'] = 'Q' + ((df['Month'] - 1) // 3 + 1).astype(str)
    return df

def calculate_quarterly_metrics(filtered_df, by_sku=False):
    """
    Calculate quarterly metrics including growth rates.
    If by_sku is True, calculate metrics for each SKU separately.
    """
    # Calculate quarter from month
    filtered_df = add_quarter(filtered_df)
    
    # Define grouping columns and aggregations
    group_cols = ['Year', 'Quarter']
    aggs = {
        'Revenue': 'sum',
        'Shipped Quantity': 'sum'
    }
    
    if by_sku:
        group_cols = ['SKU'] + group_cols
    else:
        aggs['SKU'] = 'nunique'  # Count unique SKUs only when not grouping by SKU
    
    # Calculate quarterly metrics
    quarterly_metrics = filtered_df.groupby(group_cols).agg(aggs).reset_index()
    
    # Rename columns
    quarterly_metrics = quarterly_metrics.rename(columns={
        'Revenue': 'Total Revenue',
        'Shipped Quantity': 'Units Sold'
    })
    if not by_sku:
        quarterly_metrics = quarterly_metrics.rename(columns={'SKU': 'Unique SKUs'})
    
    # Sort by Year and Quarter
    quarterly_metrics = quarterly_metrics.sort_values(['Year', 'Quarter'])
    
    # Calculate quarter-over-quarter growth
    if by_sku:
        # Calculate growth rates for each SKU separately
        quarterly_metrics['Revenue_Growth'] = quarterly_metrics.groupby('SKU')['Total Revenue'].pct_change() * 100
        quarterly_metrics['Units_Growth'] = quarterly_metrics.groupby('SKU')['Units Sold'].pct_change() * 100
    else:
        # Calculate overall growth rates
        quarterly_metrics['Revenue_Growth'] = quarterly_metrics.groupby('Year')['Total Revenue'].pct_change() * 100
        quarterly_metrics['Units_Growth'] = quarterly_metrics.groupby('Year')['Units Sold'].pct_change() * 100
    
    return quarterly_metrics

def format_quarterly_display(quarterly_metrics):
    """
    Format quarterly metrics for display.
    """
    # Add Year-Quarter column for display
    quarterly_metrics['Quarter'] = quarterly_metrics['Year'].astype(str) + ' ' + quarterly_metrics['Quarter']
    
    # Check if we have SKU-specific metrics
    if 'SKU' in quarterly_metrics.columns:
        return pd.DataFrame({
            'SKU': quarterly_metrics['SKU'],
            'Quarter': quarterly_metrics['Quarter'],
            'Revenue': quarterly_metrics['Total Revenue'],
            'QoQ Revenue Growth': quarterly_metrics['Revenue_Growth'],
            'Units Sold': quarterly_metrics['Units Sold'],
            'QoQ Units Growth': quarterly_metrics['Units_Growth']
        })
    else:
        return pd.DataFrame({
            'Quarter': quarterly_metrics['Quarter'],
            'Revenue': quarterly_metrics['Total Revenue'],
            'QoQ Revenue Growth': quarterly_metrics['Revenue_Growth'],
            'Units Sold': quarterly_metrics['Units Sold'],
            'QoQ Units Growth': quarterly_metrics['Units_Growth'],
            'Unique SKUs': quarterly_metrics['Unique SKUs']
        })

def get_sku_metrics(filtered_df):
    """
    Calculate SKU performance metrics.
    Note: Now using SKU instead of Merchant SKU for grouping.
    """
    sku_metrics = filtered_df.groupby('SKU').agg({
        'Revenue': ['sum', 'mean'],
        'Shipped Quantity': 'sum'
    }).round(2)

    sku_metrics.columns = ['Total Revenue', 'Avg Revenue per Order', 'Units Sold']
    sku_metrics = sku_metrics.reset_index()

    # Sort by Total Revenue by default
    sku_metrics = sku_metrics.sort_values('Total Revenue', ascending=False)
    
    # Calculate totals
    totals = pd.DataFrame([{
        'SKU': 'TOTAL',
        'Total Revenue': sku_metrics['Total Revenue'].sum(),
        'Avg Revenue per Order': sku_metrics['Total Revenue'].sum() / len(filtered_df) if len(filtered_df) > 0 else 0,
        'Units Sold': sku_metrics['Units Sold'].sum()
    }])
    
    # Append totals row
    sku_metrics = pd.concat([sku_metrics, totals], ignore_index=True)

    return sku_metrics

def get_daily_sales_by_year(filtered_df):
    """
    Group daily sales data by year.
    """
    return filtered_df.groupby(['Year', 'Date']).agg({
        'Revenue': 'sum',
        'Shipped Quantity': 'sum'
    }).reset_index().sort_values(['Year', 'Date'])
