import dash
import dash_cytoscape as cyto
from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Output, Input
import pandas as pd  # pip install pandas
import plotly.express as px
import networkx as nx

import webbrowser as wb

NULL_FILLER = "-"

def get_shape(band):
    # label inside of it are: ellipse, circle, database, box, text. 
    # The ones with the label outside of it are: image, circularImage, diamond, dot, star, triangle, triangleDown, square and icon
    if band in ["D","10","09","08"]:
        return "square"
    elif band in ["7B","7A"]:
        return "circle"
    elif band in ["6G","6A","6B"]:
        return "diamond"
    else:
        return "triangle"

def get_color(city):
    if city == "PUNE":
        return "city_1"
    elif city == "BANGALORE":
        return "city_2"
    elif city == "CHENNAI":
        return "city_3"
    elif city in ("HYDERABAD","MUMBAI","GURGAON","KOLKATA","NOIDA", "AHMEDABAD"):
        return "city_oth"
    else:
        return "city_unk"

def get_borderwidth(commercial_status):
    if(commercial_status == "Onboarded_Solar"):
        return 1
    else:
        return 0

def get_linkcolor(tc):
    if(tc in ["TC02 - Markets Pre Trade", "TC11 - Markets Post Trade"]):
        return 1
    elif (tc in ["TC03 - Personal Banking Processing", "TC04 - Retail and Business Lending", "TC09 - Wealth Processing", "TC12 - Barclays Financial Assistance"]):
        return 2
    elif (tc in ["TC01 - Wholesale Onboarding and Group FCO", "TC05 - Wholesale Lending", "TC36 - Corp Client Tres Svc", "TC16 - Payments and Corp Client Treas Svc", "TC17 - BX COO Shared Services"]):
        return 3
    elif (tc in ["TC07 - Merchant Services", "TC08 - Cards Platform", "TC15 - Servicing and Contact Centre"]):
        return 4
    elif (tc in ["TC13 - Secured and Unsecured Fraud"]):
        return 5
    elif(tc in ["TC14 - Digital"]):
        return 6
    elif(tc in ["TC24 - Chief Security Office", "TC32 - BI Shared Services", "TC37 - GTIS Change The Bank"]):
        return 7
    elif(tc in ["TC25 - Risk Finance and Treasury", "TC26 - Functions Technology"]):
        return 8
    else:
        return 0

def load_and_prep_data(filename):
    df = pd.read_excel(filename,engine='openpyxl')
    # df = df.iloc[0:500,:]
    
    graph_df = df[['EMP_CODE','EMP_NAME','EMP_NOTESID','PEM_NOTESID','BAND','JRSS','CITY','TC','IBM_POC','COMMERCIAL_STATUS']]
    graph_df = graph_df.set_index('EMP_CODE')
    cols_with_nan = ['EMP_NOTESID','PEM_NOTESID','BAND','JRSS','CITY','TC','IBM_POC']
    graph_df[cols_with_nan] = graph_df[cols_with_nan].fillna(NULL_FILLER)
    graph_df = graph_df.sort_values(by=['TC','PEM_NOTESID'])

    emp_id_dict = {} # Index on EMP_NOTESID to return EMP_CODE
    for emp in graph_df.itertuples():
        # if not (pd.isna(emp.EMP_NOTESID)): # If the fillna was not done before pd.isna() is a good way for individual rows
        if (emp.EMP_NOTESID != NULL_FILLER):
            emp_id_dict[emp.EMP_NOTESID] = emp.Index
    # print(emp_id_dict)     

    soc_dict = {}
    pem_df = graph_df[['PEM_NOTESID','EMP_NAME']]
    pem_groups = pem_df.groupby(['PEM_NOTESID']).count()
    for item in pem_groups.itertuples():
        soc_dict[item.Index] = item.EMP_NAME # Here index is Notes ID and EMP_NAME is count  
    
    soc_dict[NULL_FILLER] = 0 # Over riding the SOC for "-" PEM

    pem_id = []
    soc_size = []
    for emp in graph_df.itertuples():
        pem_id.append(emp_id_dict.get(emp.PEM_NOTESID, "Outsider"))
        soc_size.append(soc_dict.get(emp.EMP_NOTESID,0))
    graph_df["PEM_ID"] = pem_id
    graph_df["SOC_SIZE"] = soc_size

    # print(graph_df)

    return graph_df

def prep_graph_elements(df):
    # df = df.sort_values(by=["TC"])
    # nxg = nx.Graph()
    # for emp in df.itertuples():
    #     nxg.add_node(emp.Index)
    #     nxg.add_edge(emp.Index, emp.PEM_ID)
    # print("Working out the graph layout...")
    # pos_ = nx.spiral_layout(nxg, scale=3000) #goodish: shell scale=5000; spring k=10000 scale=3000; spiral scale=3000
    # print("Gotcha!")
    # # print(pos_)
    
    elements = [{'data': {'id': 'Outsider', 'label': 'Outsider', 'parent':'UNKNOWN'}}]
    for emp in df.itertuples():
        node = {}
        node_data = {}
        
        
        node_data["id"] = emp.Index
        node_data["label"] = emp.EMP_NAME
        node_data["notes_id"] = emp.EMP_NOTESID
        node_data["city"] = emp.CITY
        node_data["band"] = emp.BAND
        node_data["tc"] = emp.TC
        node_data["jrss"] = emp.JRSS
        node_data["soc_size"] = emp.SOC_SIZE + 20
        node_data["parent"] = emp.TC
        node["data"] = node_data

        # node_position = {}
        # x,y = pos_[emp.Index]
        # node_position["x"] = x
        # node_position["y"] = y
        # node["position"] = node_position

        node["classes"] = f"{get_color(emp.CITY)} {get_shape(emp.BAND)} border_{get_borderwidth(emp.COMMERCIAL_STATUS)}"
        elements.append(node)
        
        edge = {}
        edge_data = {}
        edge_data["source"] = emp.Index
        edge_data["target"] = emp.PEM_ID
        edge["data"] = edge_data
        edge["classes"] = f"link_{get_linkcolor(emp.TC)}"
        elements.append(edge)

    for tc in df["TC"].unique():
        node = {}
        node_data = {}
        node_data["id"] = tc
        node_data["label"] = tc
        node["data"] = node_data
        node["classes"] = f"parent_{get_linkcolor(tc)}"
        elements.append(node)

    return elements

def prep_dash(elements):
    cyto.load_extra_layouts()
    app = dash.Dash(external_stylesheets=[dbc.themes.LUX])
    app.layout = html.Div([
        dbc.Row([
            dbc.Col([
                cyto.Cytoscape(
                    id='org-chart',
                    layout={'name': 'klay'}, # circle, dagre & klay work fast, cose & spread work slow
                    style={'width': '100%', 'height': '95vh'},
                    elements = elements,
                    # minZoom = 0.02, maxZoom = 2,
                    stylesheet = [
                        {'selector': 'node',
                            'style': {'label': 'data(label)', 'height': 'data(soc_size)', 'width':'data(soc_size)'}},
                        {"selector": 'edge',
                            'style': {"curve-style": "unbundled-bezier","opacity": 1,'width': 1}},
                        {'selector': '.city_1',
                            'style': {'background-color': '#00DCA8'}},
                        {'selector': '.city_2',
                            'style': {'background-color': '#DABC3B'}},
                        {'selector': '.city_3',
                            'style': {'background-color': '#179BFF'}},
                        {'selector': '.city_oth',
                            'style': {'background-color': '#FF4D53'}},
                        {'selector': '.city_unk',
                            'style': {'background-color': '#AAAAAA'}},
                        {'selector': '.square',
                            'style': {'shape': 'square'}},
                        {'selector': '.circle',
                            'style': {'shape': 'circle'}},
                        {'selector': '.diamond',
                            'style': {'shape': 'diamond'}},
                        {'selector': '.triangle',
                            'style': {'shape': 'triangle'}},                            
                        {'selector': '.border_1',
                            'style': {'border-width': 2, 'border-color': '#111111'}},
                        {'selector': '.border_0',
                            'style': {'border-width': 1, 'border-color': '#FF0000'}},
                        {'selector': '.link_1',
                            'style': {'line-color': '#941100'}},
                        {'selector': '.link_2',
                            'style': {'line-color': '#929000'}},  
                        {'selector': '.link_3',
                            'style': {'line-color': '#008F00'}},  
                        {'selector': '.link_4',
                            'style': {'line-color': '#0096FF'}},  
                        {'selector': '.link_5',
                            'style': {'line-color': '#FF9300'}},  
                        {'selector': '.link_6',
                            'style': {'line-color': '#00FA92'}},  
                        {'selector': '.link_7',
                            'style': {'line-color': '#FF85FF'}},  
                        {'selector': '.link_8',
                            'style': {'line-color': '#9437FF'}},  
                        {'selector': '.link_0',
                            'style': {'line-color': '#A9A9A9'}},
                        {'selector': '.parent_1',
                            'style': {'background-color': '#FFD0CB'}},
                        {'selector': '.parent_2',
                            'style': {'background-color': '#FFFD99'}},
                        {'selector': '.parent_3',
                            'style': {'background-color': '#CCFFCC'}},
                        {'selector': '.parent_4',
                            'style': {'background-color': '#99D6FF'}},
                        {'selector': '.parent_5',
                            'style': {'background-color': '#FFE2BD'}},
                        {'selector': '.parent_6',
                            'style': {'background-color': '#BCFFE3'}},  
                        {'selector': '.parent_7',
                            'style': {'background-color': '#FFCCFF'}},
                        {'selector': '.parent_8',
                            'style': {'background-color': '#E3CCFF'}},                                                                              
                        {'selector': '.parent_0',
                            'style': {'background-color': '#EEEEEE'}}
                    ]
                )], width=12)
        ])
    ])

    return app

# @app.callback(
#     Output('my-graph','figure'),
#     Input('org-chart','tapNodeData'),
# )
# def update_nodes(data):
#     if data is None:
#         dff = df.copy()
#         dff.loc[dff.name == 'Program Officer (Sojourner)', 'color'] = "yellow"
#         fig = px.bar(dff, x='name', y='slaves_freed')
#         fig.update_traces(marker={'color': dff['color']})
#         return fig
#     else:
#         print(data)
#         dff = df.copy()
#         dff.loc[dff.name == data['label'], 'color'] = "yellow"
#         print(dff)
#         fig = px.bar(dff, x='name', y='slaves_freed')
#         fig.update_traces(marker={'color': dff['color']})
#         return fig

def main():
    filename = "data/VW_COMMERCIAL_BARCLAYS_INFO_202108061114.xlsx"
    df = load_and_prep_data(filename)
    # print(df)
    elements = prep_graph_elements(df)
    # print(elements)
    app = prep_dash(elements)
    wb.open_new_tab('http://127.0.0.1:8050/')
    app.run_server(debug=True)

if __name__ == '__main__':
    # main()
    main()