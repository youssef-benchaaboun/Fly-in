"""Core graph models for Fly-in."""

from dataclasses import dataclass, field


@dataclass
class Zone:
    """A zone (vertex) in the drone network."""

    coordinate: tuple[int, int]
    name: str
    color: str | None
    zone_type: str
    max_drones: int | None
    parent: str | None = None
    distance: int = 0

    def get_zone_capacity(self) -> int:
        """Return the zone's current residual capacity."""
        if self.max_drones is None:
            return 1
        return self.max_drones

    def update_zone_capacity(self, amount: int) -> None:
        """Consume residual capacity when assigning a path."""
        if self.max_drones is not None:
            self.max_drones -= amount

    def get_zone_wieght(self) -> int:
        """Return the turns needed to enter this zone."""
        return 2 if self.zone_type == "restricted" else 1


@dataclass
class Network:
    """The parsed zone graph and its residual capacities."""

    nb_drones: int = 0
    start_hub: str | None = None
    end_hub: str | None = None
    zones: dict[str, Zone] = field(default_factory=dict)
    adjacencies: dict[str, set[str]] = field(default_factory=dict)
    links_capacities: dict[tuple[str, ...], int] = field(
        default_factory=dict
    )

    def add_link(self, zone1: str, zone2: str, capacity: int) -> None:
        """Add a bidirectional link to the network."""
        self.adjacencies[zone1].add(zone2)
        self.adjacencies[zone2].add(zone1)
        key = tuple(sorted([zone1, zone2]))
        self.links_capacities[key] = capacity

    def add_zone(self, zone: Zone, kind: str) -> None:
        """Add a zone and register it as a special hub when applicable."""
        if kind == "start_hub":
            self.start_hub = zone.name
            zone.max_drones = None
        elif kind == "end_hub":
            self.end_hub = zone.name
            zone.max_drones = None
        self.zones[zone.name] = zone
        self.adjacencies[zone.name] = set()

    def get_link_capacity(self, zone1: str, zone2: str) -> int:
        """Return a bidirectional link's residual capacity."""
        key = tuple(sorted([zone1, zone2]))
        return self.links_capacities[key]

    def update_link_capacity(
        self, zone1: str, zone2: str, amount: int
    ) -> None:
        """Consume residual link capacity."""
        key = tuple(sorted([zone1, zone2]))
        self.links_capacities[key] -= amount

    def intialize(self) -> None:
        """Reset shortest-path working values.

        The original method name is retained for compatibility.
        """
        infinity = 2 * len(self.zones) + 1
        for zone in self.zones.values():
            zone.parent = None
            zone.distance = 0 if zone.name == self.start_hub else infinity
