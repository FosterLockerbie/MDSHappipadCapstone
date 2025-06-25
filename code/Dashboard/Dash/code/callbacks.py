import pandas as pd 
from dash import html
from dash.dependencies import Input, Output
from wordcloud import WordCloud
import io
import base64
import plotly.express as px
from data_loader import load_data

def register_callbacks(app):
    properties, contracts, df, city_df = load_data()
    @app.callback(
        Output("active-status-card", "children"),
        [Input("contracts-df", "data")], 
    )
    def update_active_status(data):
        df = pd.DataFrame(data).copy()
        active_df = df[df['Status'] == 'Active']
        active_count = len(active_df)
        total_count = len(df)
        active_percentage = f"{(active_count / total_count * 100):.2f}%" if total_count > 0 else "0%"
        return [
            html.H4("Active", className="card-title"),
            html.P(f"Count: {active_count}", className="card-text"),
            html.P(f"Percentage: {active_percentage}", className="card-text"),
        ]

    @app.callback(
        Output("signed-status-card", "children"),
        [Input("contracts-df", "data")],
    )
    def update_signed_status_monthly(data):
        df = pd.DataFrame(data).copy()
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df_valid_dates = df.dropna(subset=['Date'])

        if not df_valid_dates.empty:
            df_valid_dates['YearMonth'] = df_valid_dates['Date'].dt.to_period('M')
            latest_month = df_valid_dates['YearMonth'].max()
            latest_df = df_valid_dates[df_valid_dates['YearMonth'] == latest_month]
            signed_count = len(latest_df[latest_df['Status'] == 'Signed'])

            previous_months = df_valid_dates[df_valid_dates['YearMonth'] < latest_month]['YearMonth'].unique()
            previous_month = previous_months.max() if len(previous_months) > 0 else None

            mom_change_element = html.P("No previous month data", className="card-text")
            if previous_month:
                previous_df = df_valid_dates[df_valid_dates['YearMonth'] == previous_month]
                signed_previous = len(previous_df[previous_df['Status'] == 'Signed'])
                change = signed_count - signed_previous
                change_percentage_value = (change / signed_previous * 100) if signed_previous > 0 else None

                if change_percentage_value is not None:
                    change_percentage_text = f"{change_percentage_value:+.2f}%"
                    color = "red" if change > 0 else "green" if change < 0 else "inherit"
                    mom_change_element = html.P(
                        f"{change_percentage_text}",
                        className="card-text",
                        style={'color': color}
                    )
                else:
                    mom_change_element = html.P("MoM Change (vs Previous Month): N/A", className="card-text")

            return [
                html.H4("Signed", className="card-title"),
                html.P(f"Count ({latest_month}): {signed_count}", className="card-text"),
                mom_change_element,
            ]
        else:
            return [
                html.H4("Signed", className="card-title"),
                html.P("No valid date data available", className="card-text"),
            ]


    @app.callback(
        Output("avg-price-card", "children"),
        [Input("contracts-df", "data")],
    )
    def update_avg_price(data):
        df = pd.DataFrame(data).copy()
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df_valid_dates = df.dropna(subset=['Date'])

        df_valid_dates['YearMonth'] = df_valid_dates['Date'].dt.to_period('M')

        if not df_valid_dates.empty:
            latest_month = df_valid_dates['YearMonth'].max()
            latest_df = df_valid_dates[df_valid_dates['YearMonth'] == latest_month]
            avg_price_latest = latest_df['Room Rent'].mean()

            previous_month = latest_month - 1
            previous_df = df_valid_dates[df_valid_dates['YearMonth'] == previous_month]

            if not previous_df.empty:
                avg_price_previous = previous_df['Room Rent'].mean()
                price_change = avg_price_latest - avg_price_previous
                change_percentage_value = (price_change / avg_price_previous * 100) if avg_price_previous != 0 else None

                if change_percentage_value is not None:
                    if change_percentage_value > 0:
                        change_indicator = html.Span(f"+{change_percentage_value:.2f}%", style={'color': 'red'})
                    elif change_percentage_value < 0:
                        change_indicator = html.Span(f"{change_percentage_value:.2f}%", style={'color': 'green'})
                    else:
                        change_indicator = html.Span(f"{change_percentage_value:.2f}%")
                    mom_change_text = html.P(change_indicator)
                else:
                    mom_change_text = html.P("MoM Change (vs Previous Month): N/A")
            else:
                mom_change_text = html.P("No data for previous month")

            return [
                html.H4("Avg. Price", className="card-title"),
                html.P(f"Latest ({latest_month.strftime('%Y-%m')}): ${avg_price_latest:.2f}" if not pd.isna(avg_price_latest) else f"Latest ({latest_month.strftime('%Y-%m')}): N/A", className="card-text"),
                mom_change_text,
            ]
        else:
            return [
                html.H4("Avg. Price", className="card-title"),
                html.P("No valid date data available", className="card-text"),
            ]

    @app.callback(
        Output('province-property-count-bar-chart', 'figure'),
        [Input('year-slider', 'value')]
    )
    def update_province_property_count_chart(selected_year_range):
        start_year, end_year = selected_year_range
        filtered_df = properties[
            (properties['Year'] >= start_year) & (properties['Year'] <= end_year)
        ].copy()

        province_counts = filtered_df['Province'].value_counts().reset_index()
        province_counts.columns = ['Province', 'count']
        fig = px.bar(province_counts, x='Province', y='count',
                    title='Number of Properties by Province')
        fig.update_layout(xaxis_title='Province', yaxis_title='Number of Properties')
        return fig

    @app.callback(
        Output('city-property-percentage-pie-chart', 'figure'),
        [Input('province-property-count-bar-chart', 'clickData'),
        Input('year-slider', 'value')]
    )
    def update_city_pie_chart(province_click_data, selected_year_range):
        start_year, end_year = selected_year_range
        filtered_df = properties[
            (properties['Year'] >= start_year) & (properties['Year'] <= end_year)
        ].copy()
        if province_click_data:
            clicked_province = province_click_data['points'][0]['x']
            filtered_df = filtered_df [filtered_df ['Province'] == clicked_province]
            city_counts = filtered_df['City_clean'].value_counts().reset_index()
            city_counts.columns = ['City_clean', 'count']
            fig = px.pie(city_counts, names='City_clean', values='count',
                        title=f'Property Count by City in {clicked_province}'
                        )
        else:
            city_counts = filtered_df ['City_clean'].value_counts().reset_index()
            city_counts.columns = ['City_clean', 'count']
            fig = px.pie(city_counts, names='City_clean', values='count',
                        title='Overall Property Count by City'
                        )
        fig.update_traces(textinfo='none', pull=[0.1]*len(city_counts)) 
        fig.update_layout(showlegend=True) 
        return fig

    @app.callback(
        Output('city-filter-hierarchical', 'options'),
        Output('city-filter-hierarchical', 'disabled'),
        [Input('province-filter-hierarchical', 'value')]
    )
    def update_city_dropdown(selected_provinces):
        if not selected_provinces:
            return [], True
        else:
            filtered_cities = properties[properties['Province'].isin(selected_provinces)]['City_clean'].dropna().unique()
            city_options = [{'label': c, 'value': c} for c in sorted(filtered_cities)]
            return city_options, False

    @app.callback(
        Output('price-line-chart', 'figure'),
        [Input('province-filter-hierarchical', 'value'),
        Input('city-filter-hierarchical', 'value'),
        Input('year-filter', 'value'),
        Input('property-type-bar-chart', 'clickData')]
    )
    def update_price_chart(selected_provinces, selected_cities, selected_years, bar_click_data):
        filtered_df = properties.copy()

        if selected_years:
            filtered_df = filtered_df[filtered_df['Year'].isin(selected_years)]

        if selected_cities:
            filtered_df = filtered_df[filtered_df['City_clean'].isin(selected_cities)]
            group_col = 'City'
            title_prefix = 'Average Monthly Price by City'
        elif selected_provinces and len(selected_provinces) > 1:
            filtered_df = filtered_df[filtered_df['Province'].isin(selected_provinces)]
            group_col = 'Province'
            title_prefix = 'Average Monthly Price by Province'
        elif selected_provinces and len(selected_provinces) == 1:
            filtered_df = filtered_df[filtered_df['Province'].isin(selected_provinces)]
            group_col = None
            title_prefix = f'Average Monthly Price in {selected_provinces[0]}'
        else:
            group_col = None
            title_prefix = 'Overall Average Monthly Price'

        selected_property_type = None
        if bar_click_data:
            selected_property_type = bar_click_data['points'][0]['x']
            filtered_df = filtered_df[filtered_df['Property Type'] == selected_property_type]
            title_prefix += f' - Type: {selected_property_type}'

        filtered_df['Date'] = pd.to_datetime(filtered_df['Date'], errors='coerce')
        filtered_df.dropna(subset=['Date'], inplace=True)
        filtered_df['YearMonth'] = filtered_df['Date'].dt.to_period('M').dt.to_timestamp()

        if group_col:
            monthly_avg_price = filtered_df.groupby(['YearMonth', group_col])['Price'].mean().reset_index()
            fig = px.line(monthly_avg_price, x='YearMonth', y='Price', color=group_col, title=title_prefix)
        else:
            monthly_avg_price = filtered_df.groupby('YearMonth')['Price'].mean().reset_index()
            fig = px.line(monthly_avg_price, x='YearMonth', y='Price', title=title_prefix)

        fig.update_layout(xaxis_title='Month', yaxis_title='Average Price')
        return fig



    @app.callback(
        Output('wordcloud-image', 'src'),
        [Input('property-type-bar-chart', 'clickData'),
        Input('province-filter-hierarchical', 'value'),
        Input('city-filter-hierarchical', 'value'),
        Input('year-filter', 'value')]
    )
    def update_wordcloud(bar_click_data, selected_provinces, selected_cities, selected_years):
        filtered_df = properties.copy()

        if selected_provinces:
            filtered_df = filtered_df[filtered_df['Province'].isin(selected_provinces)]

        if selected_cities:
            filtered_df = filtered_df[filtered_df['City'].isin(selected_cities)]

        if selected_years:
            filtered_df = filtered_df[filtered_df['Year'].isin(selected_years)]

        selected_property_type = None
        if bar_click_data:
            selected_property_type = bar_click_data['points'][0]['x']
            filtered_df = filtered_df[filtered_df['Property Type'] == selected_property_type]

        all_words = []
        columns_to_process_list = ['Household Items', 'Furnishings', 'Safety Features', 'Amenities', 'House Rules']
        for col in columns_to_process_list:
            for item_list in filtered_df.loc[:, col].dropna():
                if isinstance(item_list, list):
                    for word in item_list:
                        cleaned_word = str(word).strip()
                        all_words.append(cleaned_word)

        for bed_type in filtered_df['Bed Type'].dropna():
            cleaned_bed_type = str(bed_type).strip()
            all_words.append(cleaned_bed_type)

        if not all_words:
            transparent_gif = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAkQBADs="
            return transparent_gif
        else:
            text = ' '.join(all_words)
            wordcloud = WordCloud(width=600, height=300, background_color=None, mode="RGBA").generate(text)
            img = io.BytesIO()
            wordcloud.to_image().save(img, format='PNG')
            img.seek(0)
            img_base64 = base64.b64encode(img.read()).decode()
            return f'data:image/png;base64,{img_base64}'

    @app.callback(
        Output('property-type-bar-chart', 'figure'),
        [Input('province-filter-hierarchical', 'value'),
        Input('city-filter-hierarchical', 'value'),
        Input('year-filter', 'value')]
    )
    def update_property_type_chart(selected_provinces, selected_cities, selected_years):
        filtered_df = properties.copy()

        if selected_years:
            filtered_df = filtered_df[filtered_df['Year'].isin(selected_years)]

        if selected_cities:
            filtered_df = filtered_df[filtered_df['City_clean'].isin(selected_cities)]
            color_col = 'City'
            title = 'Number of Properties by Type (by City)'
        elif selected_provinces and len(selected_provinces) > 1:
            filtered_df = filtered_df[filtered_df['Province'].isin(selected_provinces)]
            color_col = 'Province'
            title = 'Number of Properties by Type (by Province)'
        elif selected_provinces and len(selected_provinces) == 1:
            filtered_df = filtered_df[filtered_df['Province'].isin(selected_provinces)]
            color_col = None
            title = f'Number of Properties by Type in {selected_provinces[0]}'
        else:
            color_col = None
            title = 'Overall Number of Properties by Type'

        property_counts = filtered_df['Property Type'].value_counts().reset_index()
        property_counts.columns = ['Property Type', 'count']

        if color_col:
            property_type_province = filtered_df.groupby(['Property Type', color_col]).size().reset_index(name='count')
            fig = px.bar(property_type_province, x='Property Type', y='count', color=color_col,
                        title=title)
        else:
            fig = px.bar(property_counts, x='Property Type', y='count', title=title)

        fig.update_layout(xaxis_title='Property Type', yaxis_title='Number of Properties')
        return fig

    @app.callback(
        [
            Output('kpi-city', 'children'),
            Output('kpi-renters', 'children'),
            Output('kpi-budget', 'children'),
            Output('map-graph', 'figure'),
            Output('budget-graph', 'figure'),
            Output('lease-graph', 'figure'),
            Output('preference-graph', 'figure'),
            Output('renter_city-graph', 'figure'),
        ],
        [Input('year-filter', 'value'),
        Input('province-filter', 'value')]
    )
    def update_dashboard(selected_year, selected_province):
        dff = df.copy() 
        dff['Registered At'] = pd.to_datetime(dff['Registered At'], errors='coerce')  
        dff['Registered Year'] = dff['Registered At'].dt.year
        if selected_year is not None and selected_year != 'All':
            dff = dff[dff['Registered Year'] == selected_year]
     
        # Filter by province
        if selected_province is not None and selected_province != 'All':
            dff = dff[dff['province_id_upper'] == selected_province]

        # KPI 1: Top City
        city_counts = dff['City_extracted'].value_counts()
        if not city_counts.empty:
            top_city = city_counts.idxmax()
            top_count = int(city_counts.max())
            kpi_city = f"{top_city} ({top_count})"
        else:
            kpi_city = "N/A (0)"

        # KPI 2: Unique Renters
        kpi_renters = f"{dff['ID'].nunique():,}"

        # KPI 3: Avg Budget
        avg_budget = dff['Budget'].mean()
        kpi_budget = f"{avg_budget:.1f}" if pd.notna(avg_budget) else "N/A"

        # City-level map
        city_counts_df = (
            dff.groupby(['City_extracted', 'Latitude', 'Longitude'])
            .size()
            .reset_index(name='Registrations')
            .dropna(subset=['Latitude', 'Longitude'])
        )

        title_suffix = f" - {selected_province}" if selected_province != 'All' else ""
        map_fig = px.scatter_geo(
            city_counts_df,
            lat='Latitude',
            lon='Longitude',
            size='Registrations',
            hover_name='City_extracted',
            title='City-wise Registrations in Canada',
            scope='north america'
        )


        map_fig.update_geos(
            projection_type="natural earth",
            lataxis_range=[40, 80],
            lonaxis_range=[-130, -55]
        )


        map_fig.update_layout(
            margin={"r": 0, "t": 30, "l": 0, "b": 0},
            title={'text': 'City-wise Registrations in Canada', 'x': 0.5, 'xanchor': 'center'},
            title_x=0.55)


        # Budget box (≤4000)
        budget_fig = px.box(
            dff[dff['Budget'] <= 4000],
            y='Budget',
            title='Budget Distribution'
        ).update_layout(
            margin={'l': 60, 'r': 10, 't': 30, 'b': 40},
            title={'text': 'Budget Distribution', 'x': 0.5, 'xanchor': 'center'},
            title_x=0.6,
            yaxis=dict(range=[0, 4000]),
            height=280
        )
        budget_fig.update_traces(marker_color="#19B9F3")


        # Lease term bar
        dff['Year'] = pd.to_datetime(dff['Registered At'], errors='coerce').dt.year

# Group by Year and Lease Term
        lease_df = dff.groupby(['Year', 'Lease Term']).size().reset_index(name='Count')

        # Create line chart with multiple lines, one for each Lease Term
        lease_fig = px.line(
            lease_df,
            x='Year',
            y='Count',
            color='Lease Term',
            labels={'Year': 'Year', 'Count': 'Count', 'Lease Term': 'Lease Term'},
            title='Lease Term Trends Over Time'
        ).update_layout(
            margin={'l': 60, 'r': 10, 't': 30, 'b': 40},
            height=280,
            title={'text': 'Lease Term Trends Over Time', 'x': 0.5, 'xanchor': 'center'},
            title_x=0.55
        )

        lease_fig.update_traces(mode='lines+markers')


        preference_df = dff['Prefer Live With'].value_counts().sort_values(ascending=False).reset_index()
        preference_df.columns = ['Prefer Live With', 'Count']
        preference_fig = px.bar(
            preference_df,
            x='Prefer Live With',
            y='Count',
            labels={'Prefer Live With': 'Prefer Live With', 'Count': 'Count'},
            title='Preference Distribution'
        ).update_layout(
            margin={'l': 60, 'r': 10, 't': 30, 'b': 40},
            height=280,
            title={'text': 'Preference Distribution', 'x': 0.5, 'xanchor': 'center'},
            title_x=0.55)
        preference_fig.update_traces(marker_color='#EF553B')
    
        renter_city_df = (
            dff['city']
            .value_counts()
            .nlargest(5)
            .reset_index())


        renter_city_df.columns = ['city', 'Count']
        renter_city_fig = px.bar(
            renter_city_df,
            x='city',
            y='Count',
            labels={'City': 'city', 'Count': 'Count'},
            title='Top 5 Cities with Most Renters'
        ).update_layout(
            margin={'l': 60, 'r': 10, 't': 30, 'b': 40},
            height=280,
            title={'text': 'Top 5 Cities with Most Renters', 'x': 0.5, 'xanchor': 'center'},
            title_x=0.55)
        renter_city_fig.update_traces(marker_color="#FAED63")

        return kpi_city, kpi_renters, kpi_budget, map_fig, budget_fig, lease_fig, preference_fig, renter_city_fig


