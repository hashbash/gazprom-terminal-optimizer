from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class Terminal:
    tid: int
    remain: float
    last_collection_dt: datetime = datetime(year=2022, month=8, day=31)


@dataclass
class BankTruck:
    tid: int


@dataclass
class BankTuckPath:
    dt: datetime
    bank_truck: BankTruck
    terminals: List[Terminal]
