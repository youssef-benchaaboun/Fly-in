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
    visited:bool=False

    def __str__(self) -> str:
        """Return a readable summary of the zone."""
        return (
            f"{self.name} color: {self.color}, zone_type: {self.zone_type}\n"
            f"next: {self.neighbours}\n"
            f"max_drones: {self.max_drones}\n"
        )


class StaticMap(BaseModel):
    """Represent the static input map and its drone count."""

    nb_drones: int
    start_hub: Zone
    end_hub: Zone
    hubs: dict[str, Zone]

    def __str__(self) -> str:
        """Return a readable summary of the parsed map."""
        names = ", ".join(self.hubs)
        return (
            f"drones: {self.nb_drones}\n"
            f"start: {self.start_hub.name}\n"
            f"end: {self.end_hub.name}\n"
            f"hubs: {names}"
        )
    def apply_bfs(self)->list[list[str]]| None:
        list_path:list[list[str]]=[[self.start_hub.name]]
        solutions:list[list[str]]=[]
        self.start_hub.visited=True
        while(list_path):
            copy_list_path=[]
            for path in list_path:
                for nxt in self.hubs[path[-1]].neighbours:
                    if self.hubs[nxt].visited==False and self.hubs[nxt].zone_type!="blocked":
                        new_path=path.copy()
                        new_path.append(nxt)
                        if nxt == self.end_hub.name:
                            solutions.append(new_path)
                            continue
                        self.hubs[nxt].visited=True
                        copy_list_path.append(new_path)
            list_path=copy_list_path
        return solutions
