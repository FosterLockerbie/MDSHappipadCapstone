
import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
from style import *
from data_loader import load_data
from callbacks import register_callbacks 

app = dash.Dash(__name__,external_stylesheets=[dbc.themes.BOOTSTRAP])
app.config.suppress_callback_exceptions = True
properties, contracts, df, city_df = load_data()
min_year = int(properties['Year'].min())
max_year = int(properties['Year'].max())
year_options_slider = {'step': 1, 'marks': {str(year): str(year) for year in range(min_year, max_year + 1)}}

available_provinces = sorted(properties['Province'].dropna().unique())

#TODAY = datetime.date.today() # Get today's date (adjust based on your data)

# years = sorted(df['Registered At'].dropna().unique())
# year_options = [{'label': 'All', 'value': 'All'}] + [{'label': str(y), 'value': y} for y in years]


years = sorted(df['Registered At'].dt.year.dropna().unique())
year_options = [{'label': 'All', 'value': 'All'}] + [
    {'label': str(y), 'value': int(y)} for y in years
]
provinces = sorted(df['province_id_upper'].dropna().unique())
province_options = [{'label': 'All', 'value': 'All'}] + [{'label': p, 'value': p} for p in provinces]

app.layout = html.Div([
    dbc.Row(className="mb-3", style=logo_row_style, children=[
        dbc.Col(html.H5("Property and Renter Monitoring", style={'margin': '0'}), md=4),
        dbc.Col(md=8), 
    ]),
    dcc.Tabs(id='main-tabs', value='property', children=[
        dcc.Tab(label='Property Overview', value='property'),
        dcc.Tab(label='Renter Overview', value='renter'),
    ]),
    html.Div(id='tab-content')
])
@app.callback(
    Output('tab-content', 'children'),
    Input('main-tabs', 'value')
)
def render_tab_content(tab):
    if tab == 'property':
        return  html.Div(style={'padding': '20px'}, children=[
            dbc.Row(style={'marginBottom': '20px'}, children=[
                dbc.Col(dbc.Card(
                    html.Div(id="active-status-card", style={'padding': '15px'}),
                    style=card_style
                ), md=4),
                dbc.Col(dbc.Card(
                    html.Div(id="signed-status-card", style={'padding': '15px'}),
                    style=card_style
                ), md=4),
                dbc.Col(dbc.Card(
                    html.Div(id="avg-price-card", style={'padding': '15px'}),
                    style=card_style
                ), md=4),
            ]),

            html.Div(style=dashboard_style, children=[
                html.H4("Year Range Filter", className="mb-3", style={'textAlign': 'center'}),
                html.Div(style={'marginBottom': '20px'}, children=[
                    dcc.RangeSlider(
                        id='year-slider',
                        min=min_year,
                        max=max_year,
                        value=[min_year, max_year],
                        **year_options_slider
                    )
                ]),

                html.Div(style={'display': 'flex', 'marginBottom': '20px'}, children=[
                    html.Div(style={'width': '70%', 'paddingRight': '10px'}, children=[
                        dcc.Graph(id='province-property-count-bar-chart')
                    ]),
                    html.Div(style={'width': '30%'}, children=[
                        dcc.Graph(id='city-property-percentage-pie-chart')
                    ]),
                ]),

                html.Div(style={'marginBottom': '20px', 'display': 'flex'}, children=[
                    html.Div(style={'width': '50%', 'paddingRight': '10px'}, children=[
                        html.H4('Province and City Filters', className="mb-2", style={'textAlign': 'center'}),
                        html.Label('Filter by Province:'),
                        dcc.Dropdown(
                            id='province-filter-hierarchical',
                            options=[{'label': p, 'value': p} for p in available_provinces],
                            placeholder='Select Province(s)',
                            multi=True
                        ),
                        html.Label('Filter by City:', style={'marginTop': '10px'}),
                        dcc.Dropdown(
                            id='city-filter-hierarchical',
                            placeholder='Select City(ies)',
                            multi=True,
                            disabled=True
                        ),
                    ]),
                    html.Div(style={'width': '50%'}, children=[
                        html.H4('Year Filter', className="mb-2", style={'textAlign': 'center'}),
                        html.Label('Select Year(s):'),
                        dcc.Dropdown(
                            id='year-filter',
                            options=[{'label': str(y), 'value': y} for y in sorted(properties['Year'].dropna().astype(int).unique())],
                            placeholder='Select Year(s)',
                            multi=True
                        ),
                    ])
                ]),

                html.Div(style={'display': 'flex'}, children=[
                    html.Div(style={'width': '40%', 'paddingRight': '10px'}, children=[
                        dcc.Graph(id='price-line-chart')
                    ]),
                    html.Div(style={
                        'width': '30%',
                        'backgroundColor': 'rgba(211, 211, 211, 0.3)', # Slightly lighter grey
                        'padding': '10px',
                        'display': 'flex',
                        'flexDirection': 'column',
                        'justifyContent': 'center',
                        'alignItems': 'center',
                        'borderRadius': '5px'
                    }, children=[
                        html.H4("Property Feature Word Cloud", style={'textAlign': 'center', 'marginBottom': '10px'}),
                        html.Div(style={'display': 'flex', 'justifyContent': 'center', 'width': '100%', 'height': '100%'}, children=[
                            html.Img(id='wordcloud-image', style={'maxWidth': '100%', 'maxHeight': '100%'})
                        ])
                    ]),
                    html.Div(style={'width': '30%', 'paddingLeft': '10px'}, children=[
                        dcc.Graph(id='property-type-bar-chart')
                    ])
                ]),
                dcc.Store(id='contracts-df', data=contracts.to_dict('records'))
            ])
        ])
    elif tab == 'renter':
        return html.Div(
    style={
        'position': 'relative', 'width': '100vw', 'height': '100vh',
        'fontFamily': 'Arial', 'overflow': 'hidden', 'transform': 'scale(0.95)'
    },
    children=[
        html.Div(
                style=kpi_container_style,
                children=[
                    html.Div(style=kpi_card_style, children=[
                        html.H4("Top City", style=kpi_title_style),
                        html.H2(id='kpi-city', style=kpi_value_style_city)
                    ]),
                    html.Div(style=kpi_card_style, children=[
                        html.H4("Unique Renters", style=kpi_title_style),
                        html.H2(id='kpi-renters', style=kpi_value_style_renters)
                    ]),
                    html.Div(style=kpi_card_style, children=[
                        html.H4("Avg Budget", style=kpi_title_style),
                        html.H2(id='kpi-budget', style=kpi_value_style_budget)
                    ]),
                ]
            ),

         
            html.Div(style=map_graph_style, children=[
                dcc.Graph(id='map-graph', style={'width': '600px', 'height': '350px'})
            ]),


            html.Div(style=budget_graph_style, children=[
                dcc.Graph(id='budget-graph', style={'width': '400px', 'height': '250px'})
            ]),
            html.Div(style=lease_graph_style, children=[
                dcc.Graph(id='lease-graph', style={'width': '425px', 'height': '250px'})
            ]),


            html.Div(style=preference_style, children=[
                dcc.Graph(id='preference-graph', style={'width': '425px', 'height': '250px'})
            ]),


            html.Div(style=renter_city_style, children=[
                dcc.Graph(id='renter_city-graph', style={'width': '425px', 'height': '250px'})
            ]),


            html.Div(style=year_dropdown_style, children=[
                dcc.Dropdown(
                    id='year-filter',
                    options=year_options,
                    value=None,
                    clearable=False,
                    placeholder='Select Year'
                )
            ]),


            html.Div(style=province_dropdown_style, children=[
                dcc.Dropdown(id='province-filter',
                             options=province_options, value=None, clearable=False, placeholder='Select Province')
            ])

        ])
    
register_callbacks(app)

if __name__ == '__main__':
    app.run(debug=True)