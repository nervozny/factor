import streamlit as st
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
import io
from datasets import DataSets
from views import Render

DEBUG = False
def log(s: str):
    if DEBUG:
        print(s)

## -------------- SETTING LAYOUT ---------------
st.set_page_config(layout="wide")
tab_graphs, tab_df, tab_params = st.tabs(["Graphs", "DataFrames", "Parameters"])

## ------------- DATA LOADING ------------
@st.experimental_singleton
def load_data():
    """
    Purpose: load/pull datasets
    """
    if 'datasets' not in st.session_state:
        log("Reloading datasets...")
        return DataSets()

datasets = load_data()
st.session_state['datasets'] = datasets

df_sales = st.session_state['datasets'].df_sales
df_products = st.session_state['datasets'].df_products
df_clients = st.session_state['datasets'].df_clients
branch_dict = st.session_state['datasets'].branch_dict
brand_dict = st.session_state['datasets'].brand_dict
manager_dict = st.session_state['datasets'].manager_dict
group_dict = st.session_state['datasets'].group_dict
channel_dict = st.session_state['datasets'].channel_dict
mark_dict = st.session_state['datasets'].mark_dict


## --------------- SIDEBAR DATES -----------------
months_backward = 6

now = pd.to_datetime(datetime.now())
cur_m_first_day = pd.Timestamp(now.year, now.month, 1)

date_base_start = cur_m_first_day - relativedelta(months=months_backward)
date_base_end = date_base_start + relativedelta(months=3) - relativedelta(days=1)

date_fact_start = cur_m_first_day - relativedelta(months=3)
date_fact_end = cur_m_first_day - relativedelta(days=1)

dt_base = st.sidebar.date_input("📅 Base Interval", 
                          [date_base_start,
                           date_base_end] )

dt_fact = st.sidebar.date_input("📆 Fact Interval", 
                          [date_fact_start,
                           date_fact_end] )

## ----------------- SIDEBAR AXES ---------------------
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

try:
    with tab_graphs:

        st.markdown("# Factor analysis demo 🔐 ")
        draw_column, left_column, mid_column, right_column = st.columns(4)
        left_column.markdown(
                f'> 📅  Base : {dt_base[0].strftime("%d.%m.%Y")} - {dt_base[1].strftime("%d.%m.%Y")}\n>\n' \
                f'> 📆  Fact : {dt_fact[0].strftime("%d.%m.%Y")} - {dt_fact[1].strftime("%d.%m.%Y")}\n')
            
        ## ------------- calc_factor -----------------

        # Periods
        date_base_end_convert = pd.Timestamp(date_base_end.year, date_base_end.month, date_base_end.day, 23, 59, 59)
        date_fact_end_convert = pd.Timestamp(date_fact_end.year, date_fact_end.month, date_fact_end.day, 23, 59, 59)

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
        dm = datasets.filter_data(my_channel, my_dept, my_brand, my_manager, my_group, my_mark, date_base_start, date_base_end_convert, date_fact_start, date_fact_end_convert)
        dm1, pivot_price, pivot_cost, pivot_vol = datasets.preprocess_data(dm, df_products, df_clients, branch_dict, x_ax, y_ax)
        renderer = Render(datasets)

        mid_column.markdown(
            f"> 💰 Profit of base period = {dm1['Profit base'].sum():,.0f}\n>\n" \
            f"> 💰 Profit of fact period = {dm1['Profit fact'].sum():,.0f}")
        
        right_column.markdown(
            f"> 💰 Difference = {dm1['Profit fact'].sum() - dm1['Profit base'].sum():,.0f}\n>\n" \
            f"> ⍨"
            )

        # DRAWING
        with draw_column:
            drawing_method = st.radio(label="Drawing method:", options=['Seaborn', 'Plotly', 'Altair'], index=2)

        renderer.render(st, method=drawing_method, angle=-60)


    # show df
    with tab_df:
        st.markdown('# Output DataFrames')
        st.write("dm shape:", dm1.shape)
        st.markdown('### Price:')
        st.table(pivot_price)
        st.markdown('### Cost:')
        st.table(pivot_cost)
        st.markdown('### Volume:')
        st.table(pivot_vol)


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
        st.write('Mark:', my_mark)


    ## ------ EXPORT TO EXCEL ------
    @st.experimental_memo
    def calc_export(dept=my_dept, channel=my_channel, brand=my_brand, manager=my_manager, group=my_group, mark=my_mark):
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

except IndexError as ie:
    st.error("Pick an appropriate date interval please.")

except ValueError as ve:
    st.error("You should choose different values for X and Y axes.")

except AttributeError as ae:
    pass