import streamlit as st
from typing import List
import pandas as pd
import sys

sys.path.append('..')

import models
from opt_simulator import NaiveSimulator


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
    _funding_rate = st.slider('Funding rate, %', min_value=0.0, max_value=10.0, value=2.0, step=1.0, disabled=True)
    _truck_cost = st.slider('Truck daily expenses, rur', min_value=0, max_value=200000, value=20000, step=1000,
                            disabled=True)
    _truck_count = st.slider('Truck count', min_value=0, max_value=20, value=6, step=1)
    _collection_per_truck = st.slider('Collection per truck', min_value=0, max_value=200, value=30, step=5)

    metrics = st.multiselect(
        'Metrics',
        ['funding', 'collection', 'truck'],
        ['funding', 'collection', 'truck'])


@st.cache_data
def get_graph_data(funding_rate, truck_cost, collection_per_truck,
                   truck_count) -> List[models.DailyExpenses]:
    simulator = NaiveSimulator(funding_rate=funding_rate,
                               truck_count=truck_count,
                               truck_daily_cost=truck_cost,
                               collection_per_truck=collection_per_truck,
                               terminals_list=terminal_list,
                               dt_list=dt_columns,
                               data=df)
    simulator.calculate()
    return simulator.expenses


graph_data = get_graph_data(funding_rate=_funding_rate, collection_per_truck=_collection_per_truck,
                            truck_cost=_truck_cost, truck_count=_truck_count)

st.title('Daily expenses')
st.line_chart(graph_data, x='dt', y=metrics, use_container_width=True)

st.title('Cumulative expenses, 90 days')

cumulative_graph_data = []
total_cumulative_data = []
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
    out_expense_total = models.DailyExpensesFlat(
        dt=expense.dt,
        funding=expense.funding + cumulative_graph_data[-1].funding,
        collection=expense.collection + cumulative_graph_data[-1].collection,
        truck=expense.truck + cumulative_graph_data[-1].truck,
        collection_count=expense.collection_count,
        total_expenses=expense.funding + cumulative_graph_data[-1].funding + expense.collection +
                       cumulative_graph_data[-1].collection + expense.truck + cumulative_graph_data[-1].truck
    )
    cumulative_graph_data.append(out_expense)
    total_cumulative_data.append(out_expense_total)

st.line_chart(cumulative_graph_data, x='dt', y=metrics,  use_container_width=True)

st.title('Total cumulative expenses, 90 days')
st.line_chart(total_cumulative_data, x='dt', y=['total_expenses'],  use_container_width=True)
