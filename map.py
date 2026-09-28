from dataclasses import dataclass, field


@dataclass
class Zone:
    coordinate: tuple[int, int]
    name: str
    color: str | None = None
    zone_type: str = "normal"
    max_drones: int = 1
    neighbours: list["Zone"] = field(default_factory=list, repr=False)


@dataclass(frozen=True)
class Connection:
    zone_pair: tuple[str, str]
    max_link_capacity: int = 1


@dataclass
class StaticMap:
    nb_drones: int
    start_hub: Zone
    end_hub: Zone
    hubs: list[Zone]
    links: list[Connection]

    def print_hubs(self) -> str:
        names = ", ".join(zone.name for zone in self.hubs)
        return (
            f"drones: {self.nb_drones}\n"
            f"start: {self.start_hub.name}\n"
            f"end: {self.end_hub.name}\n"
            f"hubs: {names}\n"
            f"connections: {len(self.links)}"
        )
