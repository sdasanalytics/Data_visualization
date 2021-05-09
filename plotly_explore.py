# https://plotly.com/python/line-charts/

import plotly.express as px
import pandas as pd

def load_n_prep_data(filename):
    print(f"Loading data from : {filename}...")
    cv_df = pd.read_csv(filename,parse_dates=["Date"])
    cv_df = cv_df.set_index(["Date"])
    
    print("Calculating 'Active' metric from the daily records...")
    # cv_df['Active'] = cv_df.apply(lambda row: row.Confirmed - row.Recovered - row.Deceased, axis=1)
    cv_df['Active'] = cv_df['Confirmed'] - cv_df['Recovered'] - cv_df['Deceased']
    
    print("Calculating the State level sum of daily metrics by adding all District level data...")
    state_level_sum = cv_df.groupby(['Date','State']).sum().reset_index()
    state_level_sum["District"] = "All_Districts"
    state_level_sum = state_level_sum.set_index(["Date"])
    cv_df = cv_df.append(state_level_sum)

    print("Calculating incremental metrics from daily metrics and merging data...")
    sd_groups = cv_df.groupby(['State','District'])
    group_list = []
    for name, group in sd_groups:
        num_cols = group.iloc[:,2:]
        num_cols = num_cols.diff()
        num_cols.insert(0,'State',name[0])
        num_cols.insert(1,'District',name[1])
        group_list.append(num_cols)
    cv_df_i = pd.concat(group_list)
    cv_df_i = cv_df_i.rename(columns={"Confirmed" : "Confirmed_i", "Recovered":"Recovered_i","Deceased":"Deceased_i","Other":"Other_i","Tested":"Tested_i","Active":"Active_i"})
    cv_df = pd.merge(cv_df, cv_df_i, on = ["Date","State","District"])
    return cv_df

def prep_fig(cv_df, filter, metric, option):
    print(f"Applying filter: {filter}...")
    cv_df = cv_df.query(filter)
    
    print(f"Preparing Graph option {option} for {metric} ...")
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
    
    print("Ready to show graph...")
    return fig

def main():
    filename = 'https://api.covid19india.org/csv/latest/districts.csv'
    filter = 'District!="All_Districts"'
    metric = 'Confirmed_i'
    option = 3

    cv_df = load_n_prep_data(filename)
    # print(cv_df)
    fig = prep_fig(cv_df, filter, metric, option)
    fig.show()

if __name__ == "__main__":
    main()

