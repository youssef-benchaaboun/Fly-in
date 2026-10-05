"""Data models for a parsed Fly-in map."""

from pydantic import BaseModel


class Zone(BaseModel):
    """Represent a zone and its neighbouring zones."""

    coordinate: tuple[int, int]
    name: str
    color: str | None
    zone_type: str
    max_drones: int
    neighbours: dict[str, int]


class StaticMap(BaseModel):
    """Represent the static input map and its drone count."""

    nb_drones: int
    start_hub: Zone
    end_hub: Zone
    hubs: dict[str, Zone]

    def __str__(self) -> str:
        """Return a readable summary of the parsed map."""
        names = ", ".join(zone.name for zone in self.hubs.values())
        return (
            f"drones: {self.nb_drones}\n"
            f"start: {self.start_hub.name}\n"
            f"end: {self.end_hub.name}\n"
            f"hubs: {names}"
        )
