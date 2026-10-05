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
    def __str__(self):
        return (f"{self.name} color:{self.color},zone_type: {self.zone_type}\n"
                f"next:{self.self.neighbours}\n"
                f"max_drones : {self.self.max_drones}\n")


class StaticMap(BaseModel):
    """Represent the static input map and its drone count."""

    nb_drones: int
    start_hub: Zone
    end_hub: Zone
    hubs: dict[str, Zone]

    def __str__(self) -> str:
        """Return a readable summary of the parsed map."""
        names = ", ".join(str(zone) for zone in self.hubs)
        return (
            f"drones: {self.nb_drones}\n"
            f"start: {self.start_hub.name}\n"
            f"end: {self.end_hub.name}\n"
            f"hubs: {names}"
        )
