from typing import List
import models
from optimizer import Optimizer, GraphOptimizer


class NaiveSimulator:
    def __init__(self, collection_limit: int, funding_rate: float, collection_price: float,
                 truck_expenses: float,
                 terminals_list: List[models.Terminal], dt_list, data):
        self.collection_limit = collection_limit
        self.funding_rate = funding_rate
        self.collection_price = collection_price
        self.truck_expenses = truck_expenses
        self.terminals_list = terminals_list.copy()
        self.dt_list = dt_list
        self.data = data
        self.terminals_dict = {x.tid: x for x in self.terminals_list}
        self.expenses = None

    def calculate(self):
        result = []
        for dt in self.dt_list:
            incomes_df = self.data[['TID', dt]]
            incomes = incomes_df.set_index('TID').T.to_dict('list')
            incomes = {k: v[0] for k, v in incomes.items()}
            for terminal in self.terminals_list:
                self.terminals_dict[terminal.tid].remain += incomes[terminal.tid]

            optimizer = Optimizer(terminals=self.terminals_list)
            terminal_for_collection = optimizer.optimize_by_remain(limit=self.collection_limit)
            for collection in terminal_for_collection:
                self.terminals_dict[collection.tid].remain = 0
                self.terminals_dict[collection.tid].last_collection_dt = dt

            # calculate expenses
            funding = 0
            for tid, terminal in self.terminals_dict.items():
                funding += terminal.remain * self.funding_rate / 100 / 365
            expenses = models.DailyExpenses(
                dt=dt,
                funding=funding,
                collection=self.collection_price * len(terminal_for_collection),
                truck=self.truck_expenses,
                collection_count=len(terminal_for_collection)
            )
            result.append(expenses)
        self.expenses = result


class GraphSimulator:
    def __init__(self, collection_limit: int, funding_rate: float, collection_price: float,
                 truck_expenses: float, max_time_to_next_point_min: float,
                 terminals_list: List[models.Terminal], dt_list, data, time_matrix):
        self.collection_limit = collection_limit
        self.funding_rate = funding_rate
        self.collection_price = collection_price
        self.truck_expenses = truck_expenses
        self.terminals_list = terminals_list.copy()
        self.dt_list = dt_list
        self.data = data
        self.terminals_dict = {x.tid: x for x in self.terminals_list}
        self.expenses = None
        self.time_matrix = time_matrix
        self.max_time_to_next_point_min = max_time_to_next_point_min

    def calculate(self):
        result = []
        for dt in self.dt_list:
            incomes_df = self.data[['TID', dt]]
            incomes = incomes_df.set_index('TID').T.to_dict('list')
            incomes = {k: v[0] for k, v in incomes.items()}
            for terminal in self.terminals_list:
                self.terminals_dict[terminal.tid].remain += incomes[terminal.tid]

            optimizer = GraphOptimizer(terminals_dict=self.terminals_dict, time_matrix=self.time_matrix)
            optimizer.optimize_by_path(limit=1, stop_time=10, force_collection_days=14, window_size=1000,
                                       operating_interval_min=100,
                                       max_time_to_next_point_min=self.max_time_to_next_point_min)
            raise

            terminal_for_collection = optimizer.optimize_by_remain(limit=self.collection_limit)
            for collection in terminal_for_collection:
                self.terminals_dict[collection.tid].remain = 0
                self.terminals_dict[collection.tid].last_collection_dt = dt

            # calculate expenses
            funding = 0
            for tid, terminal in self.terminals_dict.items():
                funding += terminal.remain * self.funding_rate / 100 / 365
            expenses = models.DailyExpenses(
                dt=dt,
                funding=funding,
                collection=self.collection_price * len(terminal_for_collection),
                truck=self.truck_expenses,
                collection_count=len(terminal_for_collection)
            )
            result.append(expenses)
        self.expenses = result