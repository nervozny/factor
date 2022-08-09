import pandas as pd
import numpy as np
import streamlit as st

class DataSets():
    def __init__(self) -> None:
        self.df_sales = pd.read_parquet('data/df-sales.pq')
        self.df_products = pd.read_parquet('data/products.pq')
        self.df_clients = pd.read_parquet('data/clients.pq')

        self.branch_dict = pd.read_csv('data/branch.csv', index_col=0, header=None, names=['id', 'name'])['name'].to_dict()
        self.brand_dict = pd.read_csv('data/brand.csv', index_col=0, header=None, names=['id', 'name'])['name'].to_dict()
        self.manager_dict = pd.read_csv('data/manager.csv', index_col=0, header=None, names=['id', 'name'])['name'].to_dict()
        self.group_dict = pd.read_csv('data/group.csv', index_col=0, header=None, names=['id', 'name'])['name'].to_dict()
        self.channel_dict = pd.read_csv('data/channel.csv', index_col=0, header=None, names=['id', 'name'])['name'].to_dict()
        self.mark_dict = pd.read_csv('data/mark.csv', index_col=0, header=None, names=['id', 'name'])['name'].to_dict()

        ## -------- Assemble working Dataframe ---------
        self.df_sales['id_branch']  = self.df_sales['id_client'].map(self.df_clients['id_branch'].to_dict())
        self.df_sales['id_channel'] = self.df_sales['id_client'].map(self.df_clients['id_channel'].to_dict())
        self.df_sales['id_brand']   = self.df_sales['id_commodity'].map(self.df_products['id_brand'].to_dict())
        self.df_sales['id_group']   = self.df_sales['id_commodity'].map(self.df_products['id_group'].to_dict())
        self.df_sales['id_manager'] = self.df_sales['id_commodity'].map(self.df_products['id_manager'].to_dict())
        self.df_sales['id_mark']    = self.df_sales['id_commodity'].map(self.df_products['id_mark'].to_dict())

        self.axes_options = {
            'Branch': 'branch', 
            'Channel': 'Channel', 
            'Brand': 'Brand', 
            'Group': 'Product_group', 
            'Mark': 'Mark', 
            'Manager': 'Manager_Marketing'
        }

    def filter_data(self, channels, depts, brands, managers, groups, marks, dt_base_start, dt_base_end, dt_fact_start, dt_fact_end):
        """
        Filters initial df_sales according to passed parameters
        Parameters are lists of values
        """
        # filtering
        d_a = self.df_sales

        if channels:
            d_a = d_a.loc[d_a.id_channel.isin(channels)]
        if depts: 
            d_a = d_a.loc[d_a.id_branch.isin(depts)]
        if brands:
            d_a = d_a.loc[d_a.id_brand.isin(brands)]
        if managers:
            d_a = d_a.loc[d_a.id_manager.isin(managers)]
        if groups:
            d_a = d_a.loc[d_a.id_group.isin(groups)]
        if marks:
            d_a = d_a.loc[d_a.id_mark.isin(marks)]

        d_b = d_a.loc[(d_a.DocumentDate >= dt_base_start) & (d_a.DocumentDate <= dt_base_end)] #.copy(deep=True)
        d_f = d_a.loc[(d_a.DocumentDate >= dt_fact_start) & (d_a.DocumentDate <= dt_fact_end)] #.copy(deep=True)

        d_b = d_b.groupby(['id_commodity', 'id_client']).agg({'SalesAmount': 'sum', 'SalesCost': 'sum', 'SalesQty': 'sum', 'id_branch': 'max'}).reset_index() #.copy(deep=True)
        d_f = d_f.groupby(['id_commodity', 'id_client']).agg({'SalesAmount': 'sum', 'SalesCost': 'sum', 'SalesQty': 'sum', 'id_branch': 'max'}).reset_index() #.copy(deep=True)

        dm = pd.merge(d_b, d_f, left_on=['id_commodity', 'id_client'], right_on=['id_commodity', 'id_client'], how='outer', suffixes=('_base', '_fact'))  
        return dm



    def preprocess_data(self, dm: pd.DataFrame, df_products, df_clients, branch_dict, x_ax, y_ax):
        self.x_ax, self.y_ax = x_ax, y_ax

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
        order_col = ['id_commodity', 'id_client', 'comm_cl', 'id_department', 
                     'SalesAmount_base', 'SalesCost_base', 'SalesQty_base', 'pr_base', 'rent_base', 
                     'SalesAmount_fact', 'SalesCost_fact', 'SalesQty_fact', 'pr_fact', 'rent_fact',\
                     'price_base', 'price_fact', 'cost_base', 'cost_fact']
        dm = dm[order_col]

        # factorial analysis logic: changes due to price, cost, volume (structure)
        dm['is_absent'] = (dm.SalesQty_base == 0) + (dm.SalesQty_fact == 0) + (dm.SalesCost_base < 0) + (dm.SalesCost_fact < 0)
        dm['delta_price'] = np.where(dm.is_absent > 0, 0, (dm.price_fact - dm.price_base) * dm.SalesQty_fact)
        dm['delta_cost'] = np.where(dm.is_absent > 0, 0, (dm.cost_base - dm.cost_fact) * dm.SalesQty_fact)
        dm['delta_vol'] = np.where(dm.is_absent > 0, dm.pr_fact - dm.pr_base, (dm.SalesQty_fact - dm.SalesQty_base) * (dm.price_base - dm.cost_base))

        # adding reference cols
        my_cols_eng = ['Article', 'Brand', 'Product_group', 'Mark', 'Manager_Marketing', 'Manager_Supply', 'ABC_XYZ']
        my_cl_cols_eng = ['id_branch', 'Channel', 'Client_name']

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
        x_axis = self.axes_options[x_ax]
        y_axis = self.axes_options[y_ax]
    
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

        self.pivot_price, self.pivot_cost, self.pivot_vol = pivot_price, pivot_cost, pivot_vol
        self.dm1, self.aa, self.bb, self.cc = dm1, aa, bb, cc

        return dm1, pivot_price, pivot_cost, pivot_vol