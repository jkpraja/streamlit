import plotly.graph_objects as go
import plotly.express as px
import calendar

def create_sku_revenue_chart(data, sorted_skus=None, year_colors=None):
    """
    Create a bar chart showing revenue by SKU or by period for a single SKU.
    """
    fig = go.Figure()
    
    # Check if we're showing multiple SKUs or single SKU view
    is_single_sku = 'Period' in data.columns
    
    if is_single_sku:
        # Single SKU view - show revenue by period with year colors
        years = sorted(data['Year'].unique())
        for year in years:
            year_data = data[data['Year'] == year]
            
            fig.add_trace(
                go.Bar(
                    name=str(year),
                    x=year_data['Period'],
                    y=year_data['Revenue'],
                    marker_color=year_colors[year],  # Use year colors
                    hovertemplate="Period: %{x}<br>Revenue: $%{y:,.2f}<br>Year: " + str(year)
                )
            )
        
        title = 'Monthly Revenue Trend'
        xaxis_title = "Period"
        
    else:
        # Multiple SKUs view - show revenue by SKU with year colors for each SKU
        years = sorted(data['Year'].unique())
        for year in years:
            year_data = data[data['Year'] == year]
            # Sort this year's data by the overall SKU revenue order
            if sorted_skus:
                year_data = year_data.set_index('SKU').reindex(sorted_skus).reset_index()
            
            fig.add_trace(
                go.Bar(
                    name=str(year),
                    x=year_data['SKU'],
                    y=year_data['Revenue'],
                    marker_color=year_colors[year],  # Use year colors
                    hovertemplate="SKU: %{x}<br>Revenue: $%{y:,.2f}<br>Year: " + str(year)
                )
            )
        
        title = 'Revenue by SKU per Year'
        xaxis_title = "SKU"
    
    # Update layout for better readability
    fig.update_layout(
        title=title,
        xaxis_title=xaxis_title,
        yaxis_title="Revenue ($)",
        legend_title="Year",
        height=600,
        showlegend=True,
        barmode='group',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.5,
            xanchor="center",
            x=0.5
        ),
        yaxis=dict(tickformat="$,.0f"),
        margin=dict(b=150),  # Add bottom margin for legend
        xaxis=dict(
            tickangle=-45,
            type='category'
        ),
        hovermode='x unified'  # Show all traces at the same x-coordinate
    )
    
    return fig

def create_quarterly_chart(quarterly_metrics, year_colors, show_by_sku=False):
    """
    Create a dual-axis chart showing quarterly revenue and units sold.
    If show_by_sku is True, create separate traces for each SKU.
    """
    fig = go.Figure()
    
    if show_by_sku:
        # Create traces for each SKU and year combination
        skus = sorted(quarterly_metrics['SKU'].unique())
        years = sorted(quarterly_metrics['Year'].unique())
        
        for sku in skus:
            sku_data = quarterly_metrics[quarterly_metrics['SKU'] == sku]
            for year in years:
                year_data = sku_data[sku_data['Year'] == year]
                if not year_data.empty:
                    # Add revenue bars
                    fig.add_trace(
                        go.Bar(
                            name=f'{sku} - {year}',
                            x=year_data['Quarter'],
                            y=year_data['Total Revenue'],
                            hovertemplate=f"SKU: {sku}<br>Quarter: %{{x}}<br>Revenue: $%{{y:,.2f}}<br>Year: {year}",
                            marker_color=year_colors[year],  # Use year colors
                            offsetgroup=f"{sku}-{year}"
                        )
                    )
                    
                    # Add units sold line
                    fig.add_trace(
                        go.Scatter(
                            name=f'{sku} Units - {year}',
                            x=year_data['Quarter'],
                            y=year_data['Units Sold'],
                            mode='lines+markers',
                            yaxis='y2',
                            hovertemplate=f"SKU: {sku}<br>Quarter: %{{x}}<br>Units Sold: %{{y:,.0f}}<br>Year: {year}",
                            line=dict(
                                color=year_colors[year],  # Use year colors
                                dash='dot'
                            ),
                            marker=dict(color=year_colors[year])  # Use year colors
                        )
                    )
    else:
        # Original behavior - aggregate all SKUs
        years = sorted(quarterly_metrics['Year'].unique())
        for year in years:
            year_data = quarterly_metrics[quarterly_metrics['Year'] == year]
            
            # Add revenue bars
            fig.add_trace(
                go.Bar(
                    name=f'Revenue {year}',
                    x=year_data['Quarter'],
                    y=year_data['Total Revenue'],
                    hovertemplate="Quarter: %{x}<br>Revenue: $%{y:,.2f}<br>Year: " + str(year),
                    marker_color=year_colors[year],
                    offsetgroup=str(year)
                )
            )
            
            # Add units sold line
            fig.add_trace(
                go.Scatter(
                    name=f'Units {year}',
                    x=year_data['Quarter'],
                    y=year_data['Units Sold'],
                    mode='lines+markers',
                    yaxis='y2',
                    hovertemplate="Quarter: %{x}<br>Units Sold: %{y:,.0f}<br>Year: " + str(year),
                    line=dict(
                        color=year_colors[year],
                        dash='dot'
                    ),
                    marker=dict(color=year_colors[year])
                )
            )
    
    # Update layout for dual axis
    fig.update_layout(
        title='Quarterly Performance Overview',
        xaxis_title="Quarter",
        yaxis=dict(
            title="Revenue ($)",
            tickformat="$,.0f",
            side="left"
        ),
        yaxis2=dict(
            title="Units Sold",
            overlaying="y",
            side="right"
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.5,  # Move legend to bottom
            xanchor="center",
            x=0.5
        ),
        height=600,  # Increased height to accommodate legend
        margin=dict(b=150),  # Add bottom margin for legend
        xaxis=dict(
            tickangle=0,
            type='category',
            categoryorder='array',
            categoryarray=['Q1', 'Q2', 'Q3', 'Q4']
        ),
        barmode='group',
        hovermode='x unified'
    )
    
    return fig

def create_monthly_chart(monthly_breakdown, year_colors, show_by_sku=False):
    """
    Create a grouped bar chart showing monthly revenue by year.
    If show_by_sku is True, create separate traces for each SKU.
    """
    fig = go.Figure()
    
    if show_by_sku:
        # Create traces for each SKU and year combination
        skus = sorted(monthly_breakdown['SKU'].unique())
        years = sorted(monthly_breakdown['Year'].unique())
        
        for sku in skus:
            sku_data = monthly_breakdown[monthly_breakdown['SKU'] == sku]
            for year in years:
                year_data = sku_data[sku_data['Year'] == year]
                if not year_data.empty:
                    fig.add_trace(
                        go.Bar(
                            name=f'{sku} - {year}',
                            x=year_data['Month_Name'],
                            y=year_data['Revenue'],
                            marker_color=year_colors[year],  # Use year colors
                            hovertemplate=f"SKU: {sku}<br>Month: %{{x}}<br>Revenue: $%{{y:,.2f}}<br>Year: {year}"
                        )
                    )
    else:
        # Original behavior - aggregate all SKUs
        years = sorted(monthly_breakdown['Year'].unique())
        for year in years:
            year_data = monthly_breakdown[monthly_breakdown['Year'] == year]
            
            fig.add_trace(
                go.Bar(
                    name=str(year),
                    x=year_data['Month_Name'],
                    y=year_data['Revenue'],
                    marker_color=year_colors[year],
                    hovertemplate="Month: %{x}<br>Revenue: $%{y:,.2f}<br>Year: " + str(year)
                )
            )
    
    # Update layout for better readability
    fig.update_layout(
        title='Revenue by Month per Year',
        xaxis_title="Month",
        yaxis_title="Revenue ($)",
        legend_title="Year",
        height=600,  # Increased height to accommodate legend
        showlegend=True,
        barmode='group',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.5,  # Move legend to bottom
            xanchor="center",
            x=0.5
        ),
        margin=dict(b=150),  # Add bottom margin for legend
        yaxis=dict(tickformat="$,.0f"),
        xaxis=dict(
            tickangle=-45,
            type='category',
            categoryorder='array',
            categoryarray=[calendar.month_name[i] for i in range(1, 13)]
        ),
        hovermode='x unified'
    )
    
    return fig

def create_daily_chart(daily_sales_by_year, year_colors):
    """
    Create a line chart showing daily revenue trend by year.
    """
    fig = go.Figure()
    
    # Add a line for each year using consistent colors
    years = sorted(daily_sales_by_year['Year'].unique())
    for year in years:
        year_data = daily_sales_by_year[daily_sales_by_year['Year'] == year]
        
        fig.add_trace(
            go.Scatter(
                name=str(year),
                x=year_data['Date'],
                y=year_data['Revenue'],
                mode='lines+markers',
                line=dict(color=year_colors[year]),
                hovertemplate="Date: %{x}<br>Revenue: $%{y:,.2f}<br>Year: " + str(year)
            )
        )
    
    fig.update_layout(
        title='Daily Revenue by Year',
        xaxis_title='Date',
        yaxis_title='Revenue ($)',
        yaxis=dict(tickformat="$,.0f"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.5,  # Move legend to bottom
            xanchor="center",
            x=0.5
        ),
        height=600,  # Increased height to accommodate legend
        margin=dict(b=150),  # Add bottom margin for legend
        hovermode='x unified'
    )
    return fig

def create_geo_chart(state_sales):
    """
    Create a choropleth map showing revenue by state.
    """
    return px.choropleth(
        state_sales,
        locations='Shipping State',
        locationmode="USA-states",
        color='Revenue',
        scope="usa",
        title='Revenue by State',
        labels={'Revenue': 'Revenue ($)'}
    )
