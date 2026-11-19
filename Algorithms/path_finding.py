"""Path discovery and drone allocation for the Fly-in network."""

import math
from dataclasses import dataclass
from risdual_graph import ResidualGraph,ZoneInfo


PathFlow = tuple[list[str], int]
PathAssignment = tuple[list[str], int, int]

@dataclass
class Alogrithm:
    risdual_graph:ResidualGraph

    def allowed_hubs(self) -> list[ZoneInfo]:
        return self.risdual_graph.zones.values()

    def priority_counter(self, current: ZoneInfo) -> int:
        """Count priority zones between a zone and the path root."""
        count = 0
        while True:
            if current.zone_type == "priority":
                count += 1
            if current.parent is None:
                return count
            current = self.risdual_graph.zones[current.parent]

    def extract_min(self, hubs: list[ZoneInfo]) -> ZoneInfo:
        """Select the closest hub, preferring paths with priority zones."""
        minimum_distance = min(zone.distance for zone in hubs)
        candidates = [
            zone for zone in hubs if zone.distance == minimum_distance
        ]
        return max(candidates, key=self.priority_counter)

    def relaxtion(self, current: str) -> None:
        neighbours = (
            neighbour
            for neighbour in self.risdual_graph.adjacencies[current]
            and self.risdual_graph.get_capacity(current,neighbour)>0
        )
        for neighbour in neighbours:
            new_distance = (
                self.risdual_graph.adjacencies[current].distance
                + self.risdual_graph.adjacencies[neighbour].get_zone_wieght()
            )
            if self.risdual_graph.adjacencies[neighbour].distance > new_distance:
                self.risdual_graph.adjacencies[neighbour].parent = current
                self.risdual_graph.adjacencies[neighbour].distance = new_distance

    def construct_path(self) -> list[str]:
        """Build the current start-to-end path from parent pointers."""
        path: list[str] = []
        current = self.risdual_graph.end_hub
        while current is not None:
            path.append(current)
            current = self.risdual_graph.adjacencies[current].parent
        path.reverse()
        return path if len(path) > 1 else []

    def singal_source_shortest_path(self) -> list[str]:
        """Find one shortest available path through the residual network."""
        self.risdual_graph.intialize()
        hubs = self.allowed_hubs()
        end_hub = self.risdual_graph.end_hub
        if end_hub is None:
            return []
        while self.risdual_graph.adjacencies[end_hub] in hubs:
            current = self.extract_min(hubs)
            self.relaxtion(current.name)
            hubs.remove(current)
        return self.construct_path()

    def get_path_wight(self, path: list[str]) -> int:
        """Return the movement cost of a path."""
        return sum(self.risdual_graph.adjacencies[name].get_zone_wieght() for name in path[1:])

    def get_path_flow(self, path: list[str]) -> int:
        candidates: list[int] = []
        for index in range(len(path) - 1):
            candidates.append(
                self.risdual_graph.get_capacity(path[index], path[index + 1])
            )
        return min(candidates) if candidates else 0

    def update_path(self, path: list[str],flow:int) -> None:
        for index in range(len(path) - 1):
            self.risdual_graph.augment_edge(path[index], path[index + 1], flow)

    def max_flow(self) -> None:
        total_flow=0
        while True:
            path = self.singal_source_shortest_path()
            if not path:
                return 
            flow = self.get_path_flow(path)
            total_flow +=flow
            self.update_path(path,flow)

    @staticmethod
    def _path_cost(assigned: int, flow: int, weight: int) -> int:
        """Calculate the arrival cost of adding a batch to one path."""
        return math.ceil(assigned / flow) - 1 + weight

    def _best_path_index(
        self,
        assigned_per_path: list[int],
        flows: list[int],
        weights: list[int],
    ) -> int:
        """Return the path that preserves the original minimum-cost rule."""
        return min(
            range(len(flows)),
            key=lambda index: self._path_cost(
                assigned_per_path[index], flows[index], weights[index]
            ),
        )

    def min_arrive_time(
        self, decomposition: list[PathFlow]
    ) -> list[PathAssignment]:
        """Allocate all drones to paths without changing scheduling logic."""
        paths = [path for path, _flow in decomposition]
        flows = [flow for _path, flow in decomposition]
        weights = [self.get_path_wight(path) for path in paths]
        assigned_per_path = [0] * len(paths)

        assigned = 0
        while assigned < self.risdual_graph.nb_drones and paths:
            index = self._best_path_index(
                assigned_per_path, flows, weights
            )
            amount = min(flows[index], self.risdual_graph.nb_drones - assigned)
            assigned_per_path[index] += amount
            assigned += amount

        return [
            (path, flow, drone_count)
            for path, flow, drone_count in zip(
                paths, flows, assigned_per_path
            )
            if drone_count > 0
        ]
