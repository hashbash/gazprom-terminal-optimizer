from typing import List, Dict
from itertools import product
import models


class Optimizer:
    def __init__(self, terminals):
        self.terminals: List[models.Terminal] = terminals

    def optimize_by_remain(self, limit: int):
        self.terminals.sort(reverse=True)
        return self.terminals[:limit]


class GraphOptimizer:
    def __init__(self, terminals_dict: dict, time_matrix: Dict):
        self.terminals_dict = terminals_dict
        self.time_matrix = time_matrix

    def optimize_by_path(self, limit: int,
                         stop_time: float,
                         force_collection_days: int,
                         window_size: int,
                         operating_interval_min: float,
                         max_time_to_next_point_min: float,
                         ):
        if limit < 1:
            return []
        finished_variants = []
        local_variants = {(x.tid,): models.Path(prev_tid=x.tid, durations=[0], terminals=[x],
                                                total_drive_duration=0, total_stop_duration=0,
                                                total_terminals=1)
                          for x in self.terminals_dict.values()}

        terminals = self.terminals_dict.keys()
        counter = 0
        print(len(terminals), len(local_variants))
        while True:
            out_variants = dict()
            for key, variant in local_variants.items():
                for terminal in terminals:
                    if terminal in key:
                        continue
                    in_total_duration = variant.total_duration()
                    if in_total_duration > operating_interval_min:
                        finished_variants.append(variant)
                        continue

                    out_key = tuple(sorted(key + (terminal, )))
                    duration = self.time_matrix[variant.prev_tid][terminal]
                    if duration > max_time_to_next_point_min:
                        continue
                    out_duration = duration + in_total_duration + stop_time
                    # find local minimum
                    alternative_variant_duration = float(999)
                    alternative_variant = out_variants.get(out_key)
                    if alternative_variant:
                        alternative_variant_duration = alternative_variant.total_duration()
                    if out_duration > alternative_variant_duration:
                        continue  # if exists other variant with less duration
                    out_variant = models.Path(
                        prev_tid=terminal,
                        terminals=variant.terminals + [self.terminals_dict[terminal]],
                        durations=variant.durations + [duration],
                        total_drive_duration=variant.total_drive_duration + duration,
                        total_stop_duration=variant.total_stop_duration + stop_time,
                        total_terminals=variant.total_terminals + 1,
                    )
                    out_variants[out_key] = out_variant
            local_variants = out_variants.copy()
            print('Counter %s : %s' % (counter, len(local_variants)))
            counter += 1
            if not out_variants:
                print(finished_variants[:3])
                break
