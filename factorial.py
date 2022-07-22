import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta
import plotly.graph_objects as go
import io

## ------------- DATA LOADING ------------
df_sales = pd.read_parquet('data/df-sales.pq')
df_products = pd.read_parquet('data/products.pq')
df_clients = pd.read_parquet('data/clients.pq')

branch_dict = pd.read_csv('data/branch.csv', index_col=0, header=None, names=['id', 'name'])['name'].to_dict()
brand_dict = pd.read_csv('data/brand.csv', index_col=0, header=None, names=['id', 'name'])['name'].to_dict()
manager_dict = pd.read_csv('data/manager.csv', index_col=0, header=None, names=['id', 'name'])['name'].to_dict()
group_dict = pd.read_csv('data/group.csv', index_col=0, header=None, names=['id', 'name'])['name'].to_dict()
channel_dict = pd.read_csv('data/channel.csv', index_col=0, header=None, names=['id', 'name'])['name'].to_dict()
mark_dict = pd.read_csv('data/mark.csv', index_col=0, header=None, names=['id', 'name'])['name'].to_dict()

## -------- Assemble working Dataframe ---------
df_sales['id_branch'] = df_sales['id_client'].map(df_clients['id_branch'].to_dict())
df_sales['id_channel'] = df_sales['id_client'].map(df_clients['id_channel'].to_dict())
df_sales['id_brand'] = df_sales['id_commodity'].map(df_products['id_brand'].to_dict())
df_sales['id_group'] = df_sales['id_commodity'].map(df_products['id_group'].to_dict())
df_sales['id_manager'] = df_sales['id_commodity'].map(df_products['id_manager'].to_dict())
df_sales['id_mark'] = df_sales['id_commodity'].map(df_products['id_mark'].to_dict())

## -------------- SETTING LAYOUT ---------------
st.set_page_config(layout="wide")
tab_graphs, tab_df, tab_params = st.tabs(["Graphs", "DataFrame", "Parameters"])

## --------------- SIDEBAR -----------------
months_backward = 6
dt_base_start = (datetime.now() - relativedelta(months=months_backward))
dt_base_end = (dt_base_start + relativedelta(months=3))
y1 = pd.to_datetime(datetime.now()).year
m1 = pd.to_datetime(datetime.now()).month
cur_m_first_day = pd.Timestamp(y1, m1, 1)

dt_base_start = cur_m_first_day - relativedelta(months=months_backward)
dt_base_end = dt_base_start + relativedelta(months=3)

dt_fact_start = cur_m_first_day - relativedelta(months=3)
dt_fact_end = cur_m_first_day

date_base_start = dt_base_start
date_base_end = dt_base_end - relativedelta(days=1)
date_fact_start = dt_fact_start
date_fact_end = dt_fact_end - relativedelta(days=1)

dt_base = st.sidebar.date_input("📅 Base Interval", 
                          [date_base_start,
                           date_base_end] )

dt_fact = st.sidebar.date_input("📆 Fact Interval", 
                          [date_fact_start,
                           date_fact_end] )

## ----------------- AXES ---------------------
st.sidebar.markdown('---')
axes_options = {
    'Branch': 'branch', 
    'Channel': 'Channel', 
    'Brand': 'Brand', 
    'Group': 'Product_group', 
    'Mark': 'Mark', 
    'Manager': 'Manager_Marketing'
}

x_ax = st.sidebar.selectbox("➡️ what's on the X axis?", list(axes_options.keys()), 2)
y_ax = st.sidebar.selectbox("⬆️ what's on the Y axis?", list(axes_options.keys()), 0)

## -------------- SIDEBAR FILTERS -------------
st.sidebar.markdown('---')

# Dropbox dictionaries
m_dept = st.sidebar.multiselect("Branch", pd.Series(branch_dict) )
m_channel = st.sidebar.multiselect("Channel", pd.Series(channel_dict), default='DIY')
m_brand = st.sidebar.multiselect("Brand", pd.Series(brand_dict) )
m_manager = st.sidebar.multiselect("Manager", pd.Series(manager_dict) )
m_group = st.sidebar.multiselect("Group", pd.Series(group_dict) )
m_mark = st.sidebar.multiselect("Mark", pd.Series(mark_dict) )

with tab_graphs:
    st.markdown("# Factor analysis demo 🔐 ")
    left_column, mid_column, right_column = st.columns(3)
    left_column.markdown(
        f'> 📅  Base : {dt_base[0].strftime("%d.%m.%Y")} - {dt_base[1].strftime("%d.%m.%Y")}\n>\n' \
        f'> 📆  Fact : {dt_fact[0].strftime("%d.%m.%Y")} - {dt_fact[1].strftime("%d.%m.%Y")}\n')

    ## ------------- calc_factor -----------------

    # Periods    
    y1 = pd.to_datetime(date_base_end).year
    m1 = pd.to_datetime(date_base_end).month
    d1 = pd.to_datetime(date_base_end).day
    h1 = 23
    min1 = 59
    s1 = 59

    date_base_end_convert = pd.Timestamp(y1, m1, d1, h1, min1, s1)

    y1 = pd.to_datetime(date_fact_end).year
    m1 = pd.to_datetime(date_fact_end).month
    d1 = pd.to_datetime(date_fact_end).day
    h1 = 23
    min1 = 59
    s1 = 59

    date_fact_end_convert = pd.Timestamp(y1, m1, d1, h1, min1, s1)

    my_cols = df_products.columns
    my_cl_cols = df_clients.columns

    # convert to ids for further filtering
    my_channel = [k for k, v in channel_dict.items() if v in m_channel]
    my_dept = [k for k, v in branch_dict.items() if v in m_dept]
    my_brand = [k for k, v in brand_dict.items() if v in m_brand]
    my_manager = [k for k, v in manager_dict.items() if v in m_manager]
    my_group = [k for k, v in group_dict.items() if v in m_group]
    my_mark = [k for k, v in mark_dict.items() if v in m_mark]
    
    # filtering
    d_b = df_sales.loc[(df_sales.DocumentDate >= date_base_start) & (df_sales.DocumentDate <= date_base_end_convert)].copy(deep=True)
    d_f = df_sales.loc[(df_sales.DocumentDate >= date_fact_start) & (df_sales.DocumentDate <= date_fact_end_convert)].copy(deep=True)

    if my_dept: 
        d_b = d_b.loc[d_b.id_branch.isin(my_dept)]
        d_f = d_f.loc[d_f.id_branch.isin(my_dept)]
    if my_channel:
        d_b = d_b.loc[d_b.id_channel.isin(my_channel)]
        d_f = d_f.loc[d_f.id_channel.isin(my_channel)]
    if my_brand:
        d_b = d_b.loc[d_b.id_brand.isin(my_brand)]
        d_f = d_f.loc[d_f.id_brand.isin(my_brand)]
    if my_manager:
        d_b = d_b.loc[d_b.id_manager.isin(my_manager)]
        d_f = d_f.loc[d_f.id_manager.isin(my_manager)]
    if my_group:
        d_b = d_b.loc[d_b.id_group.isin(my_group)]
        d_f = d_f.loc[d_f.id_group.isin(my_group)]    
    if my_mark:
        d_b = d_b.loc[d_b.id_mark.isin(my_mark)]
        d_f = d_f.loc[d_f.id_mark.isin(my_mark)]


    d_b = d_b.groupby(['id_commodity', 'id_client']).agg({'SalesAmount': 'sum', 'SalesCost': 'sum', 'SalesQty': 'sum', 'id_branch': 'max'}).reset_index().copy(deep=True)
    d_f = d_f.groupby(['id_commodity', 'id_client']).agg({'SalesAmount': 'sum', 'SalesCost': 'sum', 'SalesQty': 'sum', 'id_branch': 'max'}).reset_index().copy(deep=True)

    dm = pd.merge(d_b, d_f, left_on=['id_commodity', 'id_client'], right_on=['id_commodity', 'id_client'], how='outer', suffixes=('_base', '_fact'))  

    dm['comm_cl'] = dm.id_commodity.astype(str) + dm.id_client.astype(str)
    dm['id_department'] = dm.id_branch_base
    dm.loc[dm.id_department.isnull() == True, 'id_department'] = dm.id_branch_fact

    # adding fact and base price and cost 
    dm['price_base'] = dm.SalesAmount_base/dm.SalesQty_base
    dm['price_fact'] = dm.SalesAmount_fact/dm.SalesQty_fact
    dm['cost_base'] = dm.SalesCost_base/dm.SalesQty_base
    dm['cost_fact'] = dm.SalesCost_fact/dm.SalesQty_fact

    dm.replace([np.inf, -np.inf], np.nan, inplace=True)
    dm.fillna(0, inplace=True)

    # adding base and fact profit and profitability
    dm['pr_base'] = dm.SalesAmount_base - dm.SalesCost_base
    dm['pr_fact'] = dm.SalesAmount_fact - dm.SalesCost_fact
    dm['rent_base'] = dm.pr_base / dm.SalesCost_base
    dm['rent_fact'] = dm.pr_fact / dm.SalesCost_fact

    dm.reset_index(inplace=True)
    order_col = ['id_commodity', 'id_client', 'comm_cl', 'id_department', 'SalesAmount_base', 'SalesCost_base', 'SalesQty_base', 'pr_base', 'rent_base', 'SalesAmount_fact', 'SalesCost_fact', 'SalesQty_fact', 'pr_fact', 'rent_fact',\
                'price_base', 'price_fact', 'cost_base', 'cost_fact']
    dm = dm[order_col]

    # factorial analysis logic: changes due to price, cost, volume (structure)
    dm['is_absent'] = (dm.SalesQty_base == 0) + (dm.SalesQty_fact == 0) + (dm.SalesCost_base < 0) + (dm.SalesCost_fact < 0)
    dm['delta_price'] = np.where(dm.is_absent > 0, 0, (dm.price_fact - dm.price_base) * dm.SalesQty_fact)
    dm['delta_cost'] = np.where(dm.is_absent > 0, 0, (dm.cost_base - dm.cost_fact) * dm.SalesQty_fact)
    dm['delta_vol'] = np.where(dm.is_absent > 0, dm.pr_fact - dm.pr_base, (dm.SalesQty_fact - dm.SalesQty_base) * (dm.price_base - dm.cost_base))


    # adding reference cols
    # my_cols_eng = ['ID_product', 'Article', 'Brand', 'Product_group', 'Mark', 'Manager_Marketing', 'Manager_Supply', 'ABC_XYZ']
    my_cols_eng = ['Article', 'Brand', 'Product_group', 'Mark', 'Manager_Marketing', 'Manager_Supply', 'ABC_XYZ']
    my_cl_cols_eng = ['id_branch', 'Channel', 'Client_name']

    # dm1 = df_products[my_cols_eng].set_index('ID_product').join(dm.set_index('id_commodity'), how='right').reset_index().set_index('id_client').join(df_clients[my_cl_cols_eng]).reset_index()
    dm1 = df_products[my_cols_eng].join(dm.set_index('id_commodity'), how='right').reset_index().set_index('id_client').join(df_clients[my_cl_cols_eng]).reset_index()
    dm1.rename(columns = {'level_0': 'id_client', 'index':'id_commodity'}, inplace=True)

    dm1['branch'] = dm1.id_branch.map(branch_dict)

    cols_order = [
        'branch',
        'comm_cl',
        'id_commodity',
        'id_client',
        'id_department',
        'Article',
        'Brand',
        'Product_group',
        'Mark',
        'Manager_Marketing',
        'Manager_Supply',    
        'ABC_XYZ',
        'Client_name',
        'Channel',
        'SalesAmount_base',
        'SalesCost_base',
        'SalesQty_base',
        'pr_base',
        'rent_base',
        'SalesAmount_fact',
        'SalesCost_fact',
        'SalesQty_fact',
        'pr_fact',
        'rent_fact',
        'price_base',
        'price_fact',
        'cost_base',
        'cost_fact',
        'is_absent',
        'delta_price',
        'delta_cost',
        'delta_vol'
    ]

    dm1 = dm1[cols_order]

    dm1.rename(columns = {
        'SalesAmount_base':'Revenue base',
        'SalesCost_base': 'Cost of Sales base',
        'SalesQty_base': 'Sales base, pcs',
        'pr_base': 'Profit base',
        'rent_base': 'Profitability base',
        'SalesAmount_fact' : 'Revenue fact',
        'SalesCost_fact': 'Cost of Sales fact',
        'SalesQty_fact': 'Sales fact, pcs',
        'pr_fact': 'Profit fact',
        'rent_fact': 'Profitability fact',
        'price_base': 'Price 1 piece base',
        'price_fact': 'Price 1 piece fact',
        'cost_base': 'Cost 1 piece base',
        'cost_fact': 'Cost 1 piece fact',
        'delta_price': 'Сhange in profit due to price',
        'delta_cost': 'Сhange in profit due to cost',
        'delta_vol': 'Сhange in profit due to structure',
        'comm_cl': 'id product-client',
    }, inplace=True)    

    # lookup axes ids
    x_axis = axes_options[x_ax]
    y_axis = axes_options[y_ax]
 
    a = dm1[[x_axis, 'Revenue fact']].groupby(x_axis).sum().sort_values(by='Revenue fact', ascending=False)
    a['abc_x_axis'] = (a['Revenue fact'] / a['Revenue fact'].sum()).cumsum()
    good_x = a.reset_index()
    good_x = good_x.iloc[:, 0]
        
    aa = dm1.groupby([x_axis, y_axis])[['Сhange in profit due to price']].sum().reset_index().sort_values('Сhange in profit due to price', ascending=False).loc[(dm1[x_axis].isin(good_x))]# & (dm1[y_axis].isin(good_y))]
    aa = aa.loc[(aa[x_axis].isin(good_x))]
    aa.dropna(inplace=True)
    pivot_price = pd.pivot_table(aa, values = 'Сhange in profit due to price', columns=x_axis, index=y_axis, aggfunc='sum' )

    bb = dm1.groupby([x_axis, y_axis])[['Сhange in profit due to cost']].sum().reset_index().sort_values('Сhange in profit due to cost', ascending=False).loc[(dm1[x_axis].isin(good_x))]# & (dm1[y_axis].isin(good_y))]
    bb = bb.loc[(bb[x_axis].isin(good_x))]
    bb.dropna(inplace=True)
    pivot_cost = pd.pivot_table(bb, values = 'Сhange in profit due to cost', columns=x_axis, index=y_axis, aggfunc='sum' )    
    
    cc = dm1.groupby([x_axis, y_axis])[['Сhange in profit due to structure']].sum().reset_index().sort_values('Сhange in profit due to structure', ascending=False).loc[(dm1[x_axis].isin(good_x))]# & (dm1[y_axis].isin(good_y))]
    cc = cc.loc[(cc[x_axis].isin(good_x))]
    cc.dropna(inplace=True)
    pivot_vol = pd.pivot_table(cc, values = 'Сhange in profit due to structure', columns=x_axis, index=y_axis, aggfunc='sum' )

    angle = -60

    mid_column.markdown(
        f"> 💰 Profit of base period = {dm1['Profit base'].sum():,.0f}\n>\n" \
        f"> 💰 Profit of fact period = {dm1['Profit fact'].sum():,.0f}")
    
    right_column.markdown(
        f"> 💰 Difference = {dm1['Profit fact'].sum() - dm1['Profit base'].sum():,.0f}\n>\n" \
        f"> ⍨"
        )

    # DRAWING
    left_col, mid_col, right_col = st.columns(3)

    with left_col:
        data = go.Heatmap(
                    x = pivot_price.columns.tolist(),
                    y = pivot_price.index.tolist(),
                    z = pivot_price.values.tolist(),
                    zmid=0,
                    xgap=3,
                    ygap=3,
                    colorscale='RdBu'            
                )
        layout = go.Layout(                    
                    title={'text':'Price influence   ''{:,.0f}'.format(dm1['Сhange in profit due to price'].sum()), 'xanchor':'left','yanchor':'bottom', 'y':0.87},
                    titlefont=dict(size=20, color='#518cc8'),
                    xaxis=dict(showgrid=False, tickangle = angle),
                    yaxis=dict(showgrid=False, categoryorder='category descending'),
                    font=dict(size=11),                   
                    height= 550,
                    width=550,
                    margin=dict(l=0, b=0),                    
                )
        fig = go.Figure(data=[data], layout=layout)
        st.plotly_chart(fig, use_container_width=False)

    with mid_col:
        data = go.Heatmap(
                    x = pivot_cost.columns.tolist(),
                    y = pivot_cost.index.tolist(),
                    z = pivot_cost.values.tolist(),
                    zmid=0,
                    xgap=3,
                    ygap=3,
                    colorscale='RdBu'            
                )
        layout = go.Layout(                    
                    title={'text':'Cost influence   ''{:,.0f}'.format(dm1['Сhange in profit due to cost'].sum()), 'xanchor':'left','yanchor':'bottom', 'y':0.87},
                    titlefont=dict(size=20, color='#518cc8'),
                    xaxis=dict(showgrid=False, tickangle = angle),
                    yaxis=dict(showgrid=False, categoryorder='category descending'),
                    font=dict(size=11),                   
                    height= 550,
                    width=550,
                    margin=dict(l=0, b=0),                    
                )
        fig = go.Figure(data=[data], layout=layout)
        st.plotly_chart(fig, use_container_width=False)

    with right_col:
        data = go.Heatmap(
                    x = pivot_vol.columns.tolist(),
                    y = pivot_vol.index.tolist(),
                    z = pivot_vol.values.tolist(),
                    zmid=0,
                    xgap=3,
                    ygap=3,
                    colorscale='RdBu'            
                )
        layout = go.Layout(                    
                    title={'text':'Structure influence   ''{:,.0f}'.format(dm1['Сhange in profit due to structure'].sum()), 'xanchor':'left','yanchor':'bottom', 'y':0.87},
                    titlefont=dict(size=20, color='#518cc8'),
                    xaxis=dict(showgrid=False, tickangle = angle),
                    yaxis=dict(showgrid=False, categoryorder='category descending'),
                    font=dict(size=11),                   
                    height= 550,
                    width=550,
                    margin=dict(l=0, b=0),                    
                )
        fig = go.Figure(data=[data], layout=layout)
        st.plotly_chart(fig, use_container_width=False)

# show df
with tab_df:
    st.markdown('# Output DataFrame')  

    st.write("Shape:", dm1.shape)
    st.dataframe(dm1.head(1000))

# debug info
with tab_params:
    st.markdown('# Parameters and Filters')
    st.write('Axis Х:', x_ax)
    st.write('Axis У:', y_ax)
    st.write('Branch:', my_dept)
    st.write('Channel:', my_channel)
    st.write('Brand:', my_brand)
    st.write('Manager:', my_manager)
    st.write('Group:', my_group)    
    st.write('Makr:', my_mark)


## ------ EXPORT TO EXCEL ------
def calc_export():
    strIO = io.BytesIO()
    with pd.ExcelWriter(strIO, engine='xlsxwriter') as writer:
        sheet_name = 'product-client'
        dm1.to_excel(writer, sheet_name = sheet_name, startrow=0, header=True, index=True, index_label=None)
        workbook = writer.book
        worksheet = writer.sheets[sheet_name]
        format1 = workbook.add_format({'num_format': '#,##0.00'})
        worksheet.set_column('F:F', 15)
        worksheet.set_column('R:AI', 12, format1)
        worksheet.freeze_panes(1, 0)
        header_format1 = workbook.add_format({
        'bold': True,
        'text_wrap': True,
        'valign': 'top',
        'fg_color': '#A8CED2',
        'border': 1})
        
        for col_num, value in enumerate(dm1.columns.values):
            worksheet.write(0, col_num + 1, value, header_format1)      
    
    strIO.seek(0)
    return strIO

st.sidebar.markdown('---')
st.sidebar.download_button( label="💾 Export to excel", 
                            data=calc_export(),
                            file_name='profit_analysis.xlsx',
                            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        )
st.sidebar.markdown('---')