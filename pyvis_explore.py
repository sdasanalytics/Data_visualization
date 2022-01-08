# Idea: Version A - Dataframe, native, pyvis; Version B - Dataframe, neo4j, pyvis
# Coding Version A first
from pyvis.network import Network
import pandas as pd
import math
import webbrowser as wb 

# pyvis node properties. See add_node(...) documentation at https://pyvis.readthedocs.io/en/latest/documentation.html
# id = emp_code
# label = emp_name
# title = TC, IBM_POC
# color = location
# shape = Band
# value = number of reportees

def get_shape(band):
    # label inside of it are: ellipse, circle, database, box, text. 
    # The ones with the label outside of it are: image, circularImage, diamond, dot, star, triangle, triangleDown, square and icon
    if band in ["D","10","09","08"]:
        return "square"
    elif band in ["7B","7A"]:
        return "dot"
    elif band in ["6G","6A","6B"]:
        return "diamond"
    else:
        return "triangle"

def get_color(city):
    if city == "PUNE":
        return "#009977"
    elif city == "BANGALORE":
        return "#0077BB"
    elif city == "CHENNAI":
        return "#005544"
    elif city in ("HYDERABAD","MUMBAI","GURGAON","KOLKATA","NOIDA", "AHMEDABAD"):
        return "#A83645"
    else:
        return "#CCCCCC"

def get_borderwidth(commercial_status):
    if(commercial_status == "Onboarded_Solar"):
        return 3
    else:
        return 0

df = pd.read_excel("./data/VW_COMMERCIAL_BARCLAYS_INFO_202109161125.xlsx",engine='openpyxl', index_col='EMP_CODE')
# df = df.iloc[0:100,:]

net = Network(height='100%', width='100%', bgcolor='white', font_color='black')
net.add_node("Outsider")

emp_id_dict = {}
for emp in df.itertuples():
    net.add_node(emp.Index, 
                    label = emp.EMP_NAME,
                    title = f"{emp.EMP_NAME} ({emp.JRSS}) - {emp.TC}, DL: {emp.IBM_POC}",
                    color = get_color(emp.CITY),
                    shape = get_shape(emp.BAND),
                    borderWidth = get_borderwidth(emp.COMMERCIAL_STATUS))
    emp_id_dict[emp.EMP_NOTESID] = emp.Index

for emp in df.itertuples():
    net.add_edge(emp.Index, emp_id_dict.get(emp.PEM_NOTESID, "Outsider"))

# net.barnes_hut(gravity=-20000,central_gravity=0.05, spring_length=100, overlap=0.05)
net.repulsion(node_distance=200, central_gravity=0.05, spring_length=100)
# net.show_buttons(filter_=['physics'])
net.show('nodes.html')
wb.open_new_tab('file:///Users/surjitdas/OneDrive/sandbox/Data_visualization/nodes.html')