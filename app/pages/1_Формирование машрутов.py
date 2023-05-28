import streamlit as st
import pandas as pd
import sys
import io

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

import pydeck as pdk
import random
from datetime import datetime, timedelta

try:
    from app import models
except ImportError:
    sys.path.append('../..')
    from app import models


@st.cache_data
def get_df() -> pd.DataFrame:
    return pd.read_excel('static/terminal_data_hackathon v4.xlsx',
                         sheet_name='Incomes', engine='openpyxl')


@st.cache_data
def get_geo_dict() -> dict:
    return pd.read_excel('static/terminal_data_hackathon v4.xlsx',
                         sheet_name='TIDS', engine='openpyxl').set_index('TID', drop=True).T.to_dict('list')


df = get_df()
dt_columns = df.columns[2:]
init_remain_df = df[['TID', 'остаток на 31.08.2022 (входящий)']]

terminal_list = [models.Terminal(tid=x['TID'],
                                 remain=x['остаток на 31.08.2022 (входящий)'])
                 for x in init_remain_df.to_dict('records')]


geo_dict = get_geo_dict()

with st.sidebar:
    _truck_count = st.slider('Кол-во машин', min_value=1, max_value=20, value=6, step=1)
    _stop_time = st.slider('Время на обслуживание терминала, мин', min_value=0, max_value=20, value=10, step=1)
    _min_remain = st.slider('Минимальный остаток для инкассации', min_value=0, max_value=1_000_000, step=100_000,
                            value=500_000)
    _hour_count = st.slider('Кол-во рабочих часов для машины', min_value=8, max_value=14, value=12, step=1)
    _solution_time = st.slider('Время на создание маршрута, сек', min_value=10, max_value=60, value=10, step=10)


st.title('Формирование маршрута')


def get_raw_data(min_remain: float, vehicle_count: int):
    times_df = pd.read_csv('static/times v4.csv')
    local_terminals = {x.tid: x.remain for x in terminal_list if x.remain >= min_remain}
    times_df = times_df[
        (times_df['Origin_tid'].isin(local_terminals.keys())) &
        (times_df['Destination_tid'].isin(local_terminals.keys()))
    ]
    times_df.reset_index(drop=True, inplace=True)
    uniq_terminals = list(set(set(times_df.Origin_tid.values) & set(times_df.Destination_tid.values)))
    times_df['from_idx'] = times_df.Origin_tid.apply(lambda x: uniq_terminals.index(x) + 1)
    times_df['to_idx'] = times_df.Destination_tid.apply(lambda x: uniq_terminals.index(x) + 1)

    for t in uniq_terminals:
        times_df.loc[len(times_df.index)] = [0, t, 0.0, 0, uniq_terminals.index(t)]
        times_df.loc[len(times_df.index)] = [t, 0, 0.0, uniq_terminals.index(t), 0]

    time_matrix = list(
        [list(x) for x in times_df.pivot_table('Total_Time', 'from_idx', 'to_idx', fill_value=0).values])
    del times_df
    data = dict()
    data['time_matrix'] = time_matrix
    data['demands'] = [0] + [local_terminals[x] for x in uniq_terminals]
    data['num_vehicles'] = vehicle_count
    data['depot'] = 0
    data['vehicle_capacities'] = vehicle_count * [999_999_999]
    return data, uniq_terminals


@st.cache_data
def solve(min_remain=_min_remain, vehicle_count=_truck_count, service_time=_stop_time,
          vehicle_max_minutes=_hour_count*60, solution_time=_solution_time):
    data, uniq_terminals = get_raw_data(min_remain=min_remain, vehicle_count=vehicle_count)
    manager = pywrapcp.RoutingIndexManager(len(data['time_matrix']),
                                           data['num_vehicles'], data['depot'])
    routing = pywrapcp.RoutingModel(manager)

    def time_callback(from_index, to_index):
        """Returns the distance between the two nodes."""
        # Convert from routing variable Index to distance matrix NodeIndex.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['time_matrix'][from_node][to_node] + service_time

    transit_callback_index = routing.RegisterTransitCallback(time_callback)

    # Define cost of each arc.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    routing.AddDimension(
        transit_callback_index,
        0,  # no slack
        vehicle_max_minutes,  # vehicle maximum travel time
        True,  # start cumul to zero
        'vehicle_travel_time')

    def demand_callback(from_index):
        """Returns the demand of the node."""
        # Convert from routing variable Index to demands NodeIndex.
        from_node = manager.IndexToNode(from_index)
        return data['demands'][from_node]

    demand_callback_index = routing.RegisterUnaryTransitCallback(
        demand_callback)

    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,  # null capacity slack
        data['vehicle_capacities'],  # vehicle maximum capacities
        True,  # start cumul to zero
        'Capacity')

    penalty = 1000
    for node in range(1, len(data['time_matrix'])):
        routing.AddDisjunction([manager.NodeToIndex(node)], penalty)

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
    search_parameters.time_limit.FromSeconds(3) # solution_time

    # Solve the problem.
    assignment = routing.SolveWithParameters(search_parameters)

    if not assignment:
        raise ValueError('Cannot find solution in specified time')

    dropped_nodes = []
    for node in range(routing.Size()):
        if routing.IsStart(node) or routing.IsEnd(node):
            continue
        if assignment.Value(routing.NextVar(node)) == node:
            dropped_nodes.append(manager.IndexToNode(node))

    total_time = 0
    total_load = 0
    routes = {}
    for vehicle_id in range(data['num_vehicles']):
        index = routing.Start(vehicle_id)
        plan_output = 'Route for vehicle {}:\n'.format(vehicle_id)
        route_time = 0
        route_load = 0
        vehicle_path = []
        vehicle_times = []
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            route_load += data['demands'][node_index]
            plan_output += ' {0} Load({1}) -> '.format(node_index, route_load)
            previous_index = index
            index = assignment.Value(routing.NextVar(index))
            route_time += routing.GetArcCostForVehicle(
                previous_index, index, vehicle_id)
            if node_index:
                vehicle_path.append(uniq_terminals[node_index-1])
                vehicle_times.append(routing.GetArcCostForVehicle(
                                     previous_index, index, vehicle_id))
        routes[index] = dict(vehicle_path=vehicle_path, route_load=route_load,
                             route_time=route_time, vehicle_times=vehicle_times)
        plan_output += ' {0} Load({1})\n'.format(manager.IndexToNode(index),
                                                 route_load)
        plan_output += 'Time of the route: {}m\n'.format(route_time)
        plan_output += 'Load of the route: {}\n'.format(route_load)
        print(plan_output)
        total_time += route_time
        total_load += route_load
    print('Total Time of all routes: {}m'.format(total_time))
    print('Total Load of all routes: {}'.format(total_load))

    return routes


solution = solve(min_remain=_min_remain, vehicle_count=_truck_count, service_time=_stop_time,
                 vehicle_max_minutes=_hour_count*60, solution_time=_solution_time)


final_df = pd.DataFrame.from_dict(solution, orient='index')


def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


final_df['color'] = [hex_to_rgb('#' + str(hash(str(random.randint(0, int('9'*99))).ljust(6)))[-6:]) for s in final_df.vehicle_path.values]
final_df['name'] = [f'Vehicle #{s}' for s in final_df.index.values]
final_df['path'] = [[geo_dict[j] for j in x] for x in final_df.vehicle_path.values]

pydeck_df = final_df[['name', 'color', 'path']]

# st.text(final_df)

view_state = pdk.ViewState(
    latitude=55.751244,
    longitude=37.618423,
    zoom=6
)

layer = pdk.Layer(
    type='PathLayer',
    data=pydeck_df,
    pickable=True,
    get_color='color',
    width_scale=20,
    width_min_pixels=2,
    get_path='path',
    get_width=5
)

r = pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip={'text': '{name}'}, map_style=pdk.map_styles.LIGHT)

st.pydeck_chart(r)

st.title('Маршрутный лист')
# st.dataframe(final_df)


routing_list = []
for row in final_df.to_dict('records'):
    start = datetime(day=1, month=9, year=2022, hour=8)
    for idx, v in enumerate(zip(row['vehicle_path'], row['vehicle_times'])):
        terminal, t = v
        if idx == 0:
            arrive = start
        else:
            arrive = start + timedelta(minutes=t)
        departure = arrive + timedelta(minutes=10)
        routing_list.append(dict(
            vehicle=row['name'],
            device=str(terminal),
            arrive=arrive,
            departure=departure
        ))
        start = departure

report_df = pd.DataFrame(routing_list)
st.dataframe(report_df)

buffer = io.BytesIO()

@st.cache_data
def convert_to_csv(report_df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return report_df.to_csv(index=False).encode('utf-8')


csv = convert_to_csv(report_df)

# download button 1 to download dataframe as csv
download_button = st.download_button(
    label="Скачать маршрутный лист",
    data=csv,
    file_name='routes.csv',
    mime='text/csv'
)

