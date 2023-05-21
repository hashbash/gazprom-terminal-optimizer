from typing import List
import models


class Optimizer:
    def __init__(self, terminals):
        self.terminals: List[models.Terminal] = terminals

    def optimize_by_remain(self, limit: int):
        self.terminals.sort(reverse=True)
        return self.terminals[:limit]
