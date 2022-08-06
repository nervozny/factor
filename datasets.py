import pandas as pd

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