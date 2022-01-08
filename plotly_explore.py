# Remember to change the virtual env

from dash_bootstrap_components._components.Col import Col
import plotly.express as px
import pandas as pd

import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc

import webbrowser as wb

def load_n_prep_data(filename):
    print(f"Loading data from : {filename}...")
    cv_df = pd.read_csv(filename,parse_dates=["Date"])
    cv_df = cv_df.set_index(["Date"]) # sets index on Date column, useful for merge etc later
    
    print("Calculating 'Active' metric from the daily records...")
    # cv_df['Active'] = cv_df.apply(lambda row: row.Confirmed - row.Recovered - row.Deceased, axis=1) #slower than below
    cv_df['Active'] = cv_df['Confirmed'] - cv_df['Recovered'] - cv_df['Deceased'] # faster than above
    
    print("Calculating the State level sum of daily metrics by adding all District level data...")
    state_level_sum = cv_df.groupby(['Date','State']).sum().reset_index() # reset_index is required to flatten out the table, otherwise group by creates a multiindex on [Date, State]
    state_level_sum["District"] = "All_Districts"
    state_level_sum = state_level_sum.set_index(["Date"]) # indexing back on Date as reset_index clears index from above
    cv_df = cv_df.append(state_level_sum)

    print("Calculating the country level sum of daily metrics by adding all State level data...")
    country_level_sum = state_level_sum.groupby(['Date']).sum().reset_index()
    country_level_sum["State"] = "Country"
    country_level_sum["District"] = "All_Districts"
    country_level_sum = country_level_sum.set_index(["Date"])
    cv_df = cv_df.append(country_level_sum)

    print("Calculating incremental metrics from daily metrics and merging data...")
    sd_groups = cv_df.groupby(['State','District']) # sd_groups is a DataFrameGroupBy Object, with first 2 columns as State, District
    group_list = []
  
    for name, group in sd_groups: # name is a tuple, group is a Dataframe
        num_cols = group.iloc[:,2:] # Removes the State, District index columns, so that the rest are all numerical metrics
        num_cols = num_cols.diff() # Does a diff between current row and previous row. First row will be nan
        num_cols.insert(0,'State',name[0]) # name contains the indexed columns State, District. Adding back
        num_cols.insert(1,'District',name[1])
        group_list.append(num_cols) # num_cols is a Dataframe appended to a list
   
    cv_df_i = pd.concat(group_list) # concatenates a list of Dataframes
    cv_df_i = cv_df_i.rename(columns={"Confirmed" : "Confirmed_i", "Recovered":"Recovered_i","Deceased":"Deceased_i","Other":"Other_i","Tested":"Tested_i","Active":"Active_i"})
    cv_df = pd.merge(cv_df, cv_df_i, on = ["Date","State","District"])
    return cv_df

def prep_fig(cv_df, filter='District=="All_Districts"', metric='Active', option=3):
    print(f"Applying filter: {filter}...")
    cv_df = cv_df.query(filter)
    
    print(f"Preparing Graph option {option} for {metric} ...")
    fig={}
    if(option == 1):
        cv_df = cv_df.pivot(columns=['State','District'],values=[metric])
        cv_df.columns = ['.'.join(col).strip() for col in cv_df.columns.values]
        # cv_df.columns = cv_df.columns.get_level_values(2)
        fig = px.line(cv_df, title = metric)
        fig.update_traces(mode="markers+lines", hovertemplate='Date:%{x}<br>Cases:%{y}')
        fig.update_layout(hovermode="closest", showlegend=False)
    elif(option == 2):
        cv_df['State-District'] = cv_df.apply(lambda row: row.State + "-" + row.District, axis = 1)
        fig = px.line(cv_df, y=metric, title = metric, color="State-District")
        fig.update_traces(mode="markers+lines")
        fig.update_layout(hovermode="closest", showlegend=False)
    elif(option == 3):
        fig = px.line(cv_df, y=metric, color="State", line_group="District")
        fig.update_traces(mode="lines", line={"width":4})
        fig.update_layout(hovermode="closest", showlegend=True)
        fig.update_layout(title="India Covid-19 Trends")
    elif(option == 4):
        fig = px.line(cv_df, y=metric, color="District")
        fig.update_traces(mode="lines", line={"width":4})
        fig.update_layout(hovermode="closest", showlegend=True)
    elif(option == 5):
        fig = px.bar(cv_df, y=metric, color="District", barmode='stack')  
    print("Ready to show graph...")
    return fig

def prep_dash(cv_df):
    # create dash app
    app = dash.Dash(external_stylesheets=[dbc.themes.LUX])

    # create dash layout
    # ------------------------------------------------------------------------------
    # App layout
    app.layout = html.Div([
        dbc.Row([
            dbc.Col([
                html.P("Metric:"),
                dcc.Dropdown(id="metric",
                    options=[{'label':x, 'value':x} for x in ["Confirmed","Confirmed_i","Active","Active_i","Deceased","Deceased_i"]],
                    multi=False,
                    value="Active")
                ], width=4
            ),
            dbc.Col([
                html.P("Filter:"),
                dcc.Input(id = 'filter',
                    type = 'text',
                    placeholder='District=="All_Districts',
                    debounce=True,
                    size='40',
                    value='District=="All_Districts" and State!="Country"'),
                ], width=4
            ),
            dbc.Col([
                html.P("Graph Option:"),
                dcc.RadioItems(id = 'option',
                    options=[{'label': '1'  , 'value': 1},
                            {'label': '2', 'value': 2},
                            {'label': '3' , 'value': 3},
                            {'label': '4' , 'value': 4},
                            {'label': '5' , 'value': 5}],
                    value=3),
                ], width=4
            ) 
        ]),
        dbc.Row([
            dbc.Col(
                dcc.Graph(id='graph1', figure={}, responsive=True, style={'height': '900px'}),
                width=12
            )
        ])
    ])

    # ------------------------------------------------------------------------------
    # Connect the Plotly graphs with Dash Components
    @app.callback(
        [Output(component_id='graph1', component_property='figure')],
        [Input(component_id='metric', component_property='value'),
        Input(component_id='filter', component_property='value'),
        Input(component_id='option', component_property='value')]
    )
    def update_graph(metric, filter, option):
        print(metric, filter, option)

        return [prep_fig(cv_df, filter, metric, option)] # The return needs to be a List of some reason!

    return app

def main():
    filename = 'https://data.covid19india.org/csv/latest/districts.csv'
    # filename = "data/districts.csv"
    cv_df = load_n_prep_data(filename)
    wb.open_new_tab('http://127.0.0.1:8050/')
    prep_dash(cv_df).run_server(debug=False)

if __name__ == "__main__":
    main()
    
