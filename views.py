import pandas as pd
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import seaborn as sns
import altair as alt
from datasets import DataSets

class Render():

    def __init__(self, ds: DataSets) -> None:
        self.pivot_price, self.pivot_cost, self.pivot_vol = ds.pivot_price, ds.pivot_cost, ds.pivot_vol
        self.aa, self.bb, self.cc = ds.aa, ds.bb, ds.cc
        self.x_ax, self.y_ax = ds.x_ax, ds.y_ax
        self.dm1 = ds.dm1


    def _render_seaborn(self, st):
        pivot_price, pivot_cost, pivot_vol = self.pivot_price, self.pivot_cost, self.pivot_vol
        dm1 = self.dm1
        x_ax, y_ax = self.x_ax, self.y_ax        

        plt.style.use('ggplot')
        fig, ax = plt.subplots(1, 3, figsize=(20, 5))
        fig.subplots_adjust(hspace=0.5, wspace=0.25)

        ax[0].set_title(f'Price influence   ''{:,.0f}'.format(dm1['Сhange in profit due to price'].sum()), c='#518cc8')
        ax[1].set_title(f'Cost influence   ''{:,.0f}'.format(dm1['Сhange in profit due to cost'].sum()), c='#518cc8')
        ax[2].set_title(f'Structure influence ''{:,.0f}'.format(dm1['Сhange in profit due to structure'].sum()), c='#518cc8')

        sns.heatmap(pivot_price, ax=ax[0], cmap='RdBu', cbar=False, annot=True, fmt='.0f', linewidths=.5)
        sns.heatmap(pivot_cost, ax=ax[1], cmap='RdBu', cbar=False, annot=True, fmt='.0f', linewidths=.5, yticklabels=False)
        sns.heatmap(pivot_vol.applymap(lambda x: x/1000), ax=ax[2], cmap='RdBu', cbar=False, annot=True, fmt='.1f', linewidths=.5, yticklabels=False)
        for t in ax[2].texts: t.set_text(t.get_text() + "k")

        ax[0].set_xlabel(x_ax)
        ax[1].set_xlabel(x_ax)
        ax[2].set_xlabel(x_ax + " (thousands)")
        
        ax[0].set_ylabel(y_ax)
        ax[1].set_ylabel("")
        ax[2].set_ylabel("")

        st.pyplot(fig)

    

    def _render_plotly(self, st, angle=-60):
        pivot_price, pivot_cost, pivot_vol = self.pivot_price, self.pivot_cost, self.pivot_vol
        dm1 = self.dm1

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



    def _render_altair(self, st):
        dm1, aa, bb, cc = self.dm1, self.aa, self.bb, self.cc
        
        x, y, v1, v2, v3 = aa.columns[0], aa.columns[1], aa.columns[2], bb.columns[2], cc.columns[2]

        facets = ['Price influence   ''{:,.0f}'.format(dm1['Сhange in profit due to price'].sum()),
                'Cost influence   ''{:,.0f}'.format(dm1['Сhange in profit due to cost'].sum()),
                'Structure influence  ''{:,.0f}'.format(dm1['Сhange in profit due to structure'].sum()) ]

        aa['facet'], bb['facet'], cc['facet'] = facets
        decimals = 1
        aa[v1], bb[v2], cc[v3] = aa[v1].round(decimals), bb[v2].round(decimals), cc[v3].round(decimals)

        aa.rename(columns={v1: 'value'}, inplace=True)
        bb.rename(columns={v2: 'value'}, inplace=True)
        cc.rename(columns={v3: 'value'}, inplace=True)

        tt = pd.concat([aa, bb, cc])
        
        heatmap = alt.Chart(tt).mark_rect(stroke='lightgray').encode(
            alt.X(x, type='ordinal'),
            alt.Y(y, type='ordinal'),
            alt.Color('value:Q', scale=alt.Scale(
                                    clamp=True,
                                    domainMid=0,
                                    scheme=alt.SchemeParams(name='redblue'),
                                    ), #legend=None
                                    ),
            tooltip=[x, y, 'value']
        ).properties(
            width=400,
            height=400
        ).facet(
            column=alt.Column('facet', sort=facets, 
                        header=alt.Header(labelFontSize=20, title=None, labelColor='#518cc8'))
        ).resolve_scale(
            x="independent",
            y="independent",
            color='independent'
        ).configure_scale(
            bandPaddingInner=0.01
        ).configure_view(
            stroke=None
        ).interactive()
        st.altair_chart(heatmap)



    def render(self, st, method="Altair", angle=-60):
        if method=="Seaborn":
            self._render_seaborn(st)

        if method=="Plotly":
            self._render_plotly(st, angle)

        if method=="Altair":
            self._render_altair(st)