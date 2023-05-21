import streamlit as st
from  typing import List
import pandas as pd
import models
from simulator import NaiveSimulator


@st.cache_data
def get_df() -> pd.DataFrame:
    return pd.read_excel('static/terminal_data_hackathon v4.xlsx',
                         sheet_name='Incomes', engine='openpyxl')


df = get_df()
dt_columns = df.columns[2:]
init_remain_df = df[['TID', 'остаток на 31.08.2022 (входящий)']]

terminal_list = [models.Terminal(tid=x['TID'],
                                 remain=x['остаток на 31.08.2022 (входящий)'])
                 for x in init_remain_df.to_dict('records')]


with st.sidebar:
    _funding_rate = st.slider('Funding rate, %', min_value=0.0, max_value=20.0, value=7.5, step=0.5)
    _collection_price = st.slider('Collection price, rur', min_value=0, max_value=2000, value=1000, step=100)
    _truck_daily_expenses = st.slider('Truck daily expenses, rur', min_value=0, max_value=50000, value=20000, step=1000)
    _collection_limit = st.slider('Max allowed collections', min_value=0, max_value=2000, value=50, step=10)
    metrics = st.multiselect(
        'Metrics',
        ['funding', 'collection', 'truck'],
        ['funding', 'collection', 'truck'])


@st.cache_data
def get_graph_data(funding_rate, collection_price,
                   truck_daily_expenses, collection_limit) -> List[models.DailyExpenses]:
    simulator = NaiveSimulator(collection_limit=collection_limit, collection_price=collection_price,
                               funding_rate=funding_rate,
                               truck_expenses=truck_daily_expenses,
                               terminals_list=terminal_list,
                               dt_list=dt_columns,
                               data=df)
    simulator.calculate()
    return simulator.expenses


graph_data = get_graph_data(funding_rate=_funding_rate, collection_price=_collection_price,
                            truck_daily_expenses=_truck_daily_expenses, collection_limit=_collection_limit)

st.title('Daily expenses')
st.line_chart(graph_data, x='dt', y=metrics, use_container_width=True)

st.title('Cumulative expenses, 90 days')

cumulative_graph_data = []
for idx, expense in enumerate(graph_data):
    if idx == 0:
        cumulative_graph_data.append(expense)
        continue
    out_expense = models.DailyExpenses(
        dt=expense.dt,
        funding=expense.funding + cumulative_graph_data[-1].funding,
        collection=expense.collection + cumulative_graph_data[-1].collection,
        truck=expense.truck + cumulative_graph_data[-1].truck,
        collection_count=expense.collection_count,
    )
    cumulative_graph_data.append(out_expense)

st.line_chart(cumulative_graph_data, x='dt', y=metrics,  use_container_width=True)


st.table(graph_data[:10])

st.table(cumulative_graph_data[:10])