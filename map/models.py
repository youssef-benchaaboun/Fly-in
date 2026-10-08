"""Data models for a parsed Fly-in map."""

from pydantic import BaseModel
from collections import deque



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
    def apply_bfs(self)->list[list[str]]:
        queue_path=deque([[self.start_hub.name]])
        solutions:list[list[str]]=[]
        self.start_hub.visited=True
        while(queue_path):
            path=queue_path.popleft()
            curent=path[-1]
            for nxt in self.hubs[curent].neighbours:
                if self.hubs[nxt].visited==False and self.hubs[nxt].zone_type!="blocked":
                    new_path=path+[nxt]
                    if nxt == self.end_hub.name:
                        solutions.append(new_path)
                        continue
                    self.hubs[nxt].visited=True
                    queue_path.append(new_path)
        return solutions

    def apply_dfs_stack(self)->list[list[str]]:
        stack_path=[[self.start_hub.name]]
        solutions:list[list[str]]=[]
        self.start_hub.visited=True
        while(stack_path):
            path=stack_path.pop(-1)
            curent=path[-1]
            for nxt in self.hubs[curent].neighbours:
                if self.hubs[nxt].visited==False and self.hubs[nxt].zone_type!="blocked":
                    new_path=path+[nxt]
                    if nxt == self.end_hub.name:
                        solutions.append(new_path)
                        continue
                    self.hubs[nxt].visited=True
                    stack_path.append(new_path)
        return solutions

    def apply_dfs_recursion(self,path:list[str]|None=None)->list[list[str]]:
        if path is None:
            path=[self.start_hub.name]
        solutions:list[list[str]]=[]
        self.start_hub.visited=True
        curent=path[-1]
        for nxt in self.hubs[curent].neighbours:
            if self.hubs[nxt].visited==False and self.hubs[nxt].zone_type!="blocked":
                new_path=path+[nxt]
                if nxt == self.end_hub.name:
                    solutions.append(new_path)
                    continue
                self.hubs[nxt].visited=True
                solutions.extend(self.apply_dfs_recursion(new_path))
        return solutions