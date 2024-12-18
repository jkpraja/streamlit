import streamlit as st
from datetime import datetime

def render_sidebar(df):
    """
    Render the sidebar filters and controls.
    Returns the selected filter values.
    """
    st.sidebar.header('Data Controls')
    
    # Add refresh button
    if st.sidebar.button('Refresh Data'):
        st.cache_data.clear()
    
    # Display data timestamp and summary
    st.sidebar.info(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.sidebar.info(f"Total records: {len(df):,}")
    
    # Sidebar filters
    st.sidebar.header('Filters')

    # SKU filter
    all_skus = ['All'] + sorted(df['Merchant SKU'].unique().tolist())
    selected_sku = st.sidebar.selectbox('Select SKU', all_skus)

    # Month filter
    months = [0] + sorted(df['Month'].dropna().unique().astype(int).tolist())
    selected_month = st.sidebar.selectbox(
        'Select Month', 
        months,
        format_func=lambda x: "All" if x == 0 else datetime.strptime(str(x), "%m").strftime("%B")
    )

    # Year filter
    years = [0] + sorted(df['Year'].dropna().unique().astype(int).tolist())
    selected_year = st.sidebar.selectbox(
        'Select Year',
        years,
        format_func=lambda x: "All" if x == 0 else str(x)
    )

    # Location filter
    all_states = ['All'] + sorted(df['Shipping State'].dropna().unique().tolist())
    selected_state = st.sidebar.selectbox('Select State', all_states)

    return selected_sku, selected_month, selected_year, selected_state

def render_metrics(metrics):
    """
    Render the top-level metrics in a multi-column layout.
    """
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("Total Revenue", metrics['Total Revenue'])
    col2.metric("Total Orders", metrics['Total Orders'])
    col3.metric("Average Order Value", metrics['Average Order Value'])
    col4.metric("Units Sold", metrics['Units Sold'])

def render_quarterly_metrics_table(quarterly_display):
    """
    Render the quarterly metrics table with proper formatting.
    """
    st.markdown("#### Quarterly Metrics")
    
    st.dataframe(
        quarterly_display,
        column_config={
            'Quarter': 'Quarter',
            'Revenue': st.column_config.NumberColumn(
                'Revenue',
                format='$%.2f'
            ),
            'QoQ Revenue Growth': st.column_config.NumberColumn(
                'QoQ Revenue Growth',
                format='%.1f%%'
            ),
            'Units Sold': st.column_config.NumberColumn(
                'Units Sold',
                format='%d'
            ),
            'QoQ Units Growth': st.column_config.NumberColumn(
                'QoQ Units Growth',
                format='%.1f%%'
            ),
            'Unique SKUs': st.column_config.NumberColumn(
                'Unique SKUs',
                format='%d'
            )
        },
        hide_index=True,
        use_container_width=True
    )

def render_sku_metrics_table(sku_metrics):
    """
    Render the SKU performance metrics table with proper formatting.
    """
    st.dataframe(
        sku_metrics,
        column_config={
            'SKU': 'SKU',
            'Total Revenue': st.column_config.NumberColumn(
                'Total Revenue',
                format='$%.2f'
            ),
            'Avg Revenue per Order': st.column_config.NumberColumn(
                'Avg Revenue per Order',
                format='$%.2f'
            ),
            'Units Sold': st.column_config.NumberColumn(
                'Units Sold',
                format='%d'
            )
        },
        hide_index=True,
        use_container_width=True
    )

def render_chart(fig):
    """
    Render a plotly chart with consistent width settings.
    """
    st.plotly_chart(fig, use_container_width=True)
