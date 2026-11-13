"""Path discovery and drone allocation for the Fly-in network."""

import math

from models import Network, Zone


PathFlow = tuple[list[str], int]
PathAssignment = tuple[list[str], int, int]


class Alogrithm:
    """Find usable paths and distribute drones between them.

    The class name is retained for compatibility with the original project.
    """

    def __init__(self, network: Network) -> None:
        """Store the network structures used by the algorithm."""
        self.network = network
        self.zones = network.zones
        self.adjacencies = network.adjacencies
        self.link_capacity = network.links_capacities

    def allowed_hubs(self) -> list[Zone]:
        """Return zones which may still participate in a path."""
        return [
            zone
            for zone in self.zones.values()
            if zone.zone_type != "blocked" and zone.get_zone_capacity() > 0
        ]

    def priority_counter(self, current: Zone) -> int:
        """Count priority zones between a zone and the path root."""
        count = 0
        while True:
            if current.zone_type == "priority":
                count += 1
            if current.parent is None:
                return count
            current = self.zones[current.parent]

    def extract_min(self, hubs: list[Zone]) -> Zone:
        """Select the closest hub, preferring paths with priority zones."""
        minimum_distance = min(zone.distance for zone in hubs)
        candidates = [
            zone for zone in hubs if zone.distance == minimum_distance
        ]
        return max(candidates, key=self.priority_counter)

    def relaxtion(self, current: str) -> None:
        """Relax all accessible outgoing links from one zone."""
        neighbours = (
            neighbour
            for neighbour in self.adjacencies[current]
            if self.zones[neighbour].zone_type != "blocked"
            and self.network.get_link_capacity(current, neighbour) > 0
        )
        for neighbour in neighbours:
            new_distance = (
                self.zones[current].distance
                + self.zones[neighbour].get_zone_wieght()
            )
            if self.zones[neighbour].distance > new_distance:
                self.zones[neighbour].parent = current
                self.zones[neighbour].distance = new_distance

    def construct_path(self) -> list[str]:
        """Build the current start-to-end path from parent pointers."""
        path: list[str] = []
        current = self.network.end_hub
        while current is not None:
            path.append(current)
            current = self.zones[current].parent
        path.reverse()
        return path if len(path) > 1 else []

    def singal_source_shortest_path(self) -> list[str]:
        """Find one shortest available path through the residual network."""
        self.network.intialize()
        hubs = self.allowed_hubs()
        end_hub = self.network.end_hub
        if end_hub is None:
            return []
        while self.zones[end_hub] in hubs:
            current = self.extract_min(hubs)
            self.relaxtion(current.name)
            hubs.remove(current)
        return self.construct_path()

    def get_path_wight(self, path: list[str]) -> int:
        """Return the movement cost of a path."""
        return sum(self.zones[name].get_zone_wieght() for name in path[1:])

    def get_path_flow(self, path: list[str]) -> int:
        """Return the maximum residual flow supported by a path."""
        candidates: list[int] = []
        for index in range(len(path) - 1):
            candidates.append(
                self.network.get_link_capacity(path[index], path[index + 1])
            )
            if path[index] not in (
                self.network.start_hub,
                self.network.end_hub,
            ):
                candidates.append(self.zones[path[index]].get_zone_capacity())
        return min(candidates) if candidates else 0

    def update_path_flow(self, path: list[str]) -> None:
        """Remove a path's assigned flow from residual capacities."""
        flow = self.get_path_flow(path)
        for index in range(len(path) - 1):
            self.network.update_link_capacity(
                path[index], path[index + 1], flow
            )
            self.zones[path[index]].update_zone_capacity(amount=flow)

    def flow_decomapstion(self) -> list[PathFlow]:
        """Decompose the residual network into usable paths and flows."""
        decomposition: list[PathFlow] = []
        while True:
            path = self.singal_source_shortest_path()
            if not path:
                return decomposition
            flow = self.get_path_flow(path)
            decomposition.append((path, flow))
            self.update_path_flow(path)

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
        while assigned < self.network.nb_drones and paths:
            index = self._best_path_index(
                assigned_per_path, flows, weights
            )
            amount = min(flows[index], self.network.nb_drones - assigned)
            assigned_per_path[index] += amount
            assigned += amount

        return [
            (path, flow, drone_count)
            for path, flow, drone_count in zip(
                paths, flows, assigned_per_path
            )
            if drone_count > 0
        ]
