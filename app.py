import pandas as pd
from flask import Flask
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import datetime
import plotly.graph_objects as go


# Create app 
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server # Here you have access to the flask server 


# Load Data
df=pd.read_excel('Bird Strikes_Final.xlsx')
dff = pd.read_csv('state_codes.csv')
state_codes = { row['state'] : row['code'] for index, row in dff.iterrows()}
df['code'] = df['Origin State'].apply(lambda x : state_codes[x])


def create_dropdown_options(df, key):
    ls = df[key].unique()
    return ls, \
            [{'label': str(effect),'value': str(effect)} for effect in ls]

impact_list, impact_options = create_dropdown_options(df, 'Effect: Impact to flight')
when_phase_list, when_phase_options = create_dropdown_options(df, 'When: Phase of flight')
                   

# Create app layout
app.layout = html.Div(
            [
                html.Div(
                    [
                        html.H1(
                            'Plotly Dash',

                        ),
                        html.H4(
                            'Bird Strikes in 2000-2011',
                        )
                    ],
                    style={'padding': 10}
                ),
                html.Div(
                    [
                        html.H6(
                            'Impact To Flight',
                        ),
                        dcc.Dropdown(
                                    id='effect_flight',
                                    value=impact_list,
                                    className="dcc_control",
                                    multi=True,
                                    options=impact_options,
                        ),
                        html.H6(
                            'Phase Of Flight',
                        ),
                        dcc.Dropdown(
                                    id='when_phase',
                                    value=when_phase_list,
                                    className="dcc_control",
                                    multi=True,
                                    options=when_phase_options,
                        ),
                        dcc.Graph(id='main_graph'),
                        html.Label('From 2000 to 2011', id='time-range-label'),
                        dcc.RangeSlider(
                                    id='year_slider',
                                    min=2000,
                                    max=2011,
                                    marks={i: '{}'.format(i) for i in range(2000, 2012)},
                                    value=[2000, 2011],
                                    className="dcc_control",
                        ),  
                        html.Label('Birds Killed in: ', id='state-label'),
                        dcc.Graph(id='bird-plot'), 
                    ],
                    style={'padding': 10}
                ),
                # Hidden div inside the app that stores the intermediate value
                html.Div(id='intermediate-value', style={'display': 'none'}),
        ]
    )

# Callback for main map plot 
@app.callback([Output('main_graph', 'figure'),
               Output('intermediate-value', 'children')],
              [Input('effect_flight', 'value'),
               Input('when_phase', 'value'),
               Input('year_slider', 'value')])
def make_main_figure(effect_flight, when_phase, year_slider):

    df_bird_totals, df_filtered = filter_dataframe(df, effect_flight, when_phase, year_slider)

    data = go.Choropleth(
        locations=list(df_bird_totals['Cost: Total $']['count'].index), 
        z = list(df_bird_totals['Cost: Total $']['count']),
        locationmode = 'USA-states', 
        colorscale = 'Reds',
        colorbar_title = "Count",
    )
    
    layout = dict(
        title_text = 'US Bird Strikes',
        geo_scope='usa', # limite map scope to USA
    )

    figure = go.Figure(data=data, layout=layout)
    return figure, df_filtered.to_dict()


#callback for bird deaths bar chart 
@app.callback(
    output=Output('bird-plot', 'figure'),
    inputs=[Input('main_graph', 'clickData'),
    Input('intermediate-value', 'children')])
def update_plots(main_graph, intermediate):
    dff = pd.DataFrame.from_dict(intermediate)
    dff2= dff[dff['code'].isin([main_graph['points'][0]['location']])]
    df_birds = dff2[['Wildlife: Species', 'Wildlife: Number Struck Actual']].groupby(['Wildlife: Species']).agg(['sum'])

    fig = go.Figure(go.Bar(
            x=list(df_birds['Wildlife: Number Struck Actual']['sum']),
            y=list(df_birds['Wildlife: Number Struck Actual']['sum'].index),
            orientation='h',
            ))

    fig.update_layout(margin={'t': 0})
    return fig

# the value of RangeSlider causes Label to update
@app.callback(
    output=Output('time-range-label', 'children'),
    inputs=[Input('year_slider', 'value')]
    )
def _update_time_range_label(year_range):
    return 'From {} to {}'.format(year_range[0], year_range[1])


# the value of state selected causes Label to update
@app.callback(
    output=Output('state-label', 'children'),
    inputs=[Input('main_graph', 'clickData')]
    )
def _update_time_range_label(main_graph):
    return 'Birds Killed in: {}'.format(main_graph['points'][0]['location'])


def filter_dataframe(dff, effect_flight, when_phase, year_slider):
    df_filtered = dff[dff['Effect: Impact to flight'].isin(effect_flight) 
            & dff['When: Phase of flight'].isin(when_phase) 
            & (dff['FlightDate'] > datetime.datetime(year_slider[0], 1, 1))
            & (dff['FlightDate'] < datetime.datetime(year_slider[1], 12, 31))]
    df_bird_totals = df_filtered[['code', 'Cost: Total $']].groupby(['code']).agg(['count', 'sum'])
    return df_bird_totals, df_filtered


# Main
if __name__ == '__main__':
    app.server.run(debug=True, threaded=True)