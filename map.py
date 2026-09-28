from pydantic import BaseModel, Field
class Zone(BaseModel):
    coordinate: tuple[int, int]
    name: str = Field(min_length=1)
    color: str | None = None
    zone_type: str = "normal"
    max_drones: int = Field(default=1, ge=1)
    neighbours:list[Zone]

class Connection(BaseModel):
    zone_pair: tuple[str, str] 
    max_link_capacity: int = Field(default=1, ge=1)

class StaticMap(BaseModel):
    start_hub: Zone
    end_hub: Zone
    hubs: list[Zone]
    links: list[Connection]

