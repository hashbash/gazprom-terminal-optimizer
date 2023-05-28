import ortools

import sys

sys.path.append('../..')

import pandas as pd
import numpy as np
from app import models


df = pd.read_excel('../static/terminal_data_hackathon v4.xlsx',
                       sheet_name='Incomes', engine='openpyxl')
dt_columns = df.columns[2:]
init_remain_df = df[['TID', 'остаток на 31.08.2022 (входящий)']]

terminal_dict = {x['TID']: x['остаток на 31.08.2022 (входящий)']
                 for x in init_remain_df.to_dict('records')}

times_df = pd.read_csv('../static/times v4.csv')

sample_df = times_df[(times_df.Origin_tid % 20 == 0) & (times_df.Destination_tid % 20 == 0)].reset_index(drop=True)
uniq_terminals = list(set(set(sample_df.Origin_tid.values) & set(sample_df.Destination_tid.values)))

print(uniq_terminals)
print(len(uniq_terminals))
sample_df['from_idx'] = sample_df.Origin_tid.apply(lambda x: uniq_terminals.index(x) + 1)
sample_df['to_idx'] = sample_df.Destination_tid.apply(lambda x: uniq_terminals.index(x) + 1)

for t in uniq_terminals:
    sample_df.loc[len(sample_df.index)] = [0, t, 0.0, 0, uniq_terminals.index(t)]
    sample_df.loc[len(sample_df.index)] = [t, 0, 0.0, uniq_terminals.index(t), 0]


time_matrix = list([list(x) for x in sample_df.pivot_table('Total_Time', 'from_idx', 'to_idx', fill_value=0).values])


print('Finished load data')

"""Capacited Vehicles Routing Problem (CVRP)."""

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp


def create_data_model():
    """Stores the data for the problem."""
    data = {}
    data['time_matrix'] = time_matrix
    data['demands'] = [0] + [terminal_dict[x] for x in uniq_terminals]
    data['vehicle_capacities'] = [9990000, 9990000, 9990000, 9990000]
    data['num_vehicles'] = 4
    data['depot'] = 0
    return data


def print_solution(data, manager, routing, assignment):
    """Prints assignment on console."""
    print(f'Objective: {assignment.ObjectiveValue()}')
    # Display dropped nodes.
    dropped_nodes = 'Dropped nodes:'
    dropped_count = 0
    for node in range(routing.Size()):
        if routing.IsStart(node) or routing.IsEnd(node):
            continue
        if assignment.Value(routing.NextVar(node)) == node:
            dropped_count += 1
            dropped_nodes += ' {}'.format(manager.IndexToNode(node))
    print(dropped_count, ':', dropped_nodes)
    # Display routes
    total_distance = 0
    total_load = 0
    for vehicle_id in range(data['num_vehicles']):
        index = routing.Start(vehicle_id)
        plan_output = 'Route for vehicle {}:\n'.format(vehicle_id)
        route_distance = 0
        route_load = 0
#         global _routing  # //
#         _routing = routing  # //
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            route_load += data['demands'][node_index]
            plan_output += ' {0} Load({1}) -> '.format(node_index, route_load)
            previous_index = index
            index = assignment.Value(routing.NextVar(index))
            route_distance += routing.GetArcCostForVehicle(
                previous_index, index, vehicle_id)
        plan_output += ' {0} Load({1})\n'.format(manager.IndexToNode(index),
                                                 route_load)
        plan_output += 'Time of the route: {}m\n'.format(route_distance)
        plan_output += 'Load of the route: {}\n'.format(route_load)
        print(plan_output)
        total_distance += route_distance
        total_load += route_load
    print('Total Distance of all routes: {}m'.format(total_distance))
    print('Total Load of all routes: {}'.format(total_load))


def main():
    """Solve the CVRP problem."""
    # Instantiate the data problem.
    data = create_data_model()

    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(len(data['time_matrix']),
                                           data['num_vehicles'], data['depot'])

    # Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)


    # Create and register a transit callback.
    def distance_callback(from_index, to_index):
        """Returns the distance between the two nodes."""
        # Convert from routing variable Index to distance matrix NodeIndex.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['time_matrix'][from_node][to_node] + 10

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    # Define cost of each arc.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    routing.AddDimension(
        transit_callback_index,
        0,  # no slack
        500,  # vehicle maximum travel time
        True,  # start cumul to zero
        'vehicle_travel_time')

    # Add Capacity constraint.
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
    # # Allow to drop nodes.
    penalty = 1000
    for node in range(1, len(data['time_matrix'])):
        routing.AddDisjunction([manager.NodeToIndex(node)], penalty)

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
    search_parameters.time_limit.FromSeconds(5)

    # Solve the problem.
    assignment = routing.SolveWithParameters(search_parameters)

    # Print solution on console.
    if assignment:
        print_solution(data, manager, routing, assignment)
    else:
        print('Cannot find solution')


main()
