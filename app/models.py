from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class Terminal:
    tid: int
    remain: float
    last_collection_dt: datetime = datetime(year=2022, month=8, day=31)

    def __lt__(self, other):
        return self.remain < other.remain


@dataclass
class DailyExpenses:
    dt: datetime
    funding: float
    collection: float
    truck: float
    collection_count: int

    def total_expenses(self):
        return self.total_collection + self.total_funding + self.truck_expenses


@dataclass
class Path:
    prev_tid: int
    durations: List[float]
    terminals: List[Terminal]
    total_drive_duration: float
    total_stop_duration: float
    total_terminals: int

    def total_duration(self):
        return self.total_drive_duration + self.total_stop_duration
