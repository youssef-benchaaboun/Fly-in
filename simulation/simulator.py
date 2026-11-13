"""Turn-by-turn coloured terminal simulation."""

from dataclasses import dataclass

from Algorithms.path_finding import PathAssignment
from models import Network


@dataclass
class DroneGroup:
    """A group of drones following the same path at the same position."""

    identifiers: list[str]
    path: list[str]
    path_index: int = 0
    in_transit: bool = False


class Simulator:
    """Render the precomputed path assignment one turn at a time."""

    _RESET = "\033[0m"
    _WHITE = "\033[37m"
    _COLORS = {
        "black": "\033[30m",
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "white": _WHITE,
        "gray": "\033[90m",
        "grey": "\033[90m",
    }

    def __init__(
        self, solution: list[PathAssignment], network: Network
    ) -> None:
        """Initialize simulation counters and path queues."""
        self.solution = solution
        self.network = network
        self.started = [0] * len(solution)
        self.groups: list[DroneGroup] = []
        self.next_identifier = 1

    def _create_groups(self) -> None:
        """Start at most one flow-sized group on every path this turn."""
        for index, (path, flow, assigned) in enumerate(self.solution):
            remaining = assigned - self.started[index]
            if remaining <= 0:
                continue
            amount = min(flow, remaining)
            identifiers = [
                f"D{number}"
                for number in range(
                    self.next_identifier, self.next_identifier + amount
                )
            ]
            group = DroneGroup(identifiers=identifiers, path=path)
            self.groups.append(group)
            self.started[index] += amount
            self.next_identifier += amount

    def _display_token(self, group: DroneGroup) -> str:
        """Advance a group and return its destination/connection token."""
        destination = group.path[group.path_index + 1]
        if group.in_transit:
            group.in_transit = False
            group.path_index += 1
            return destination
        if self.network.zones[destination].zone_type == "restricted":
            group.in_transit = True
            source = group.path[group.path_index]
            return f"{source}-{destination}"
        group.path_index += 1
        return destination

    def _colour(self, text: str, zone_name: str) -> str:
        """Colour text for a zone, using white for unknown colour names."""
        colour_name = self.network.zones[zone_name].color
        escape = self._COLORS.get(
            colour_name.lower() if colour_name else "white", self._WHITE
        )
        return f"{escape}{text}{self._RESET}"

    def _move_groups(self) -> list[str]:
        """Move active groups once and format every movement."""
        movements: list[str] = []
        for group in self.groups:
            if group.path_index >= len(group.path) - 1:
                continue
            token = self._display_token(group)
            destination = group.path[group.path_index + int(group.in_transit)]
            movements.extend(
                self._colour(f"{identifier}-{token}", destination)
                for identifier in group.identifiers
            )
        return movements

    def _all_arrived(self) -> bool:
        """Report whether all assigned drones reached their destination."""
        all_started = all(
            started == assigned
            for started, (_path, _flow, assigned) in zip(
                self.started, self.solution
            )
        )
        return all_started and all(
            group.path_index == len(group.path) - 1
            for group in self.groups
        )

    def simulation(self) -> None:
        """Run and print the simulation until all drones arrive."""
        if not self.solution:
            return
        while not self._all_arrived():
            self._create_groups()
            movements = self._move_groups()
            if movements:
                print(" ".join(movements))
