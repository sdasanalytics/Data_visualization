# https://plotly.com/python/line-charts/

import plotly.express as px
import pandas as pd

cv_df = pd.read_csv('districts.csv',parse_dates=["Date"])
cv_df = cv_df.set_index(["Date"])
print(cv_df.head(5))

# cv_df = cv_df.query('State=="Maharashtra" and District in ["Mumbai","Pune"]')
# cv_df = cv_df.query('State=="West Bengal" or State=="Delhi"')
cv_df['Active'] = cv_df.apply(lambda row: row.Confirmed - row.Recovered - row.Deceased, axis=1)
print(cv_df.head(5))

option = 3
if(option == 1):
    cv_df = cv_df.pivot(columns=['State','District'],values=['Confirmed'])
    print(cv_df.head(5))
    # print(cv_df.columns.get_level_values(2))
    # cv_df.columns = cv_df.columns.map(' '.join).str.strip()
    cv_df.columns = ['.'.join(col).strip() for col in cv_df.columns.values]
    # cv_df.columns = cv_df.columns.get_level_values(2)
    print(cv_df.head(5))
    fig = px.line(cv_df)
    fig.update_traces(mode="markers+lines", hovertemplate='Date:%{x}<br>Cases:%{y}')
    fig.update_layout(hovermode="closest", showlegend=False)
elif(option == 2):
    cv_df['State-District'] = cv_df.apply(lambda row: row.State + "-" + row.District, axis = 1)
    print(cv_df.head(5))
    fig = px.line(cv_df, y="Confirmed", color="State-District")
    fig.update_traces(mode="markers+lines")
    fig.update_layout(hovermode="closest", showlegend=False)
elif(option == 3):
    fig = px.line(cv_df, y="Active", color="State", line_group="District")
    fig.update_traces(mode="lines", line={"width":4})
    fig.update_layout(hovermode="closest", showlegend=True)

fig.show()