
"""Normalize an undirected Fly-in network into a directed graph."""

from dataclasses import dataclass, field
from models import Network


@dataclass
class ZoneInfo:
    name: str
    zone_type: str = "normal"
    distance: float = float("inf")
    parent: str | None = None
    potential: float = 0


@dataclass
class MapNormalized:
    network: Network

    zones: dict[str, ZoneInfo] = field(default_factory=dict)
    adjacencies: dict[str, set[str]] = field(default_factory=dict)

    links_capacity: dict[tuple[str, str], int] = field(
        default_factory=dict
    )
    links_type: dict[tuple[str, str], str] = field(
        default_factory=dict
    )
    links_cost: dict[tuple[str, str], int] = field(
        default_factory=dict
    )
    links_flow: dict[tuple[str, str], int] = field(
        default_factory=dict
    )

    start_hub: str | None = None
    end_hub: str | None = None

    def __post_init__(self) -> None:
        self.normalize()

    def capacity_key(self, src: str, dst: str) -> tuple[str, str]:

        if src.endswith("out") and dst.endswith("in"):
            zone1 = src[:-3]
            zone2 = dst[:-2]
            first, second = sorted((zone1, zone2))
            return (first, second)

        return (src, dst)

    def add_capacity(self, src: str, dst: str, capacity: int) -> None:
        key = self.capacity_key(src, dst)
        if key not in self.links_capacity:
            self.links_capacity[key] = capacity

    def get_capacity(self, src: str, dst: str) -> int:
        key = self.capacity_key(src, dst)
        return self.links_capacity[key]

    def update_capacity(self, src: str, dst: str, amount: int) -> None:
        key = self.capacity_key(src, dst)
        remaining = self.links_capacity[key] - amount
        self.links_capacity[key] = remaining

    def add_edge(
        self,
        src: str,
        dst: str,
        capacity: int,
        cost: int,
        link_type: str,
    ) -> None:
        self.adjacencies[src].add(dst)
        key = (src, dst)

        self.links_cost[key] = cost
        self.links_type[key] = link_type
        self.links_flow[key] = 0

        self.add_capacity(src, dst, capacity)

    def normalize_zones(self) -> None:

        for zone in self.network.zones.values():
            if zone.zone_type == "blocked":
                continue

            zone_in = f"{zone.name}in"
            zone_out = f"{zone.name}out"

            self.zones[zone_in] = ZoneInfo(zone_in, zone.zone_type)
            self.zones[zone_out] = ZoneInfo(zone_out, zone.zone_type)
            self.adjacencies[zone_in] = set()
            self.adjacencies[zone_out] = set()

            capacity = zone.get_zone_capacity()
            cost = zone.get_zone_wieght()

            if zone.name == self.network.start_hub:
                self.start_hub = zone_in
                self.zones[self.start_hub].distance = 0
                capacity = self.network.nb_drones
                cost = 0

            elif zone.name == self.network.end_hub:
                self.end_hub = zone_out
                capacity = self.network.nb_drones
                cost = 0

            self.add_edge(zone_in, zone_out, capacity, cost, zone.zone_type)

    def normalize_links(self) -> None:
        links = self.network.links_capacities.items()
        for (zone1, zone2), capacity in links:
            if (
                self.network.zones[zone1].zone_type == "blocked"
                or self.network.zones[zone2].zone_type == "blocked"
            ):
                continue
            self.add_edge(f"{zone1}out", f"{zone2}in", capacity, 0, "link")
            self.add_edge(f"{zone2}out", f"{zone1}in", capacity, 0, "link")

    def normalize(self) -> None:
        self.normalize_zones()
        self.normalize_links()

    def intialize(self) -> None:
        for zone in self.zones:
            self.zones[zone].distance = float("inf")
            if zone == self.start_hub:
                self.zones[zone].distance = 0
            self.zones[zone].parent = None
