"""Data models for a parsed Fly-in map."""

from pydantic import BaseModel



class Zone(BaseModel):
    """Represent a zone and its neighbouring zones."""

    coordinate: tuple[int, int]
    name: str
    color: str | None
    zone_type: str
    max_drones: int

    def get_zone_capacity(self)->int:
        return self.max_drones

    def update_zone_capacity(self,amount:int)->None:
        self.max_drones = self.max_drones - amount

    def get_zone_wieght(self)->int:
        if self.zone_type=="restricted":
            return 2
        return 1


class Network(BaseModel):
    """Represent the static input map and its drone count."""

    nb_drones: int=0
    start_hub: str|None=None
    end_hub: str|None=None
    zones: dict[str, Zone]={}
    adjacencies:dict[str,set[str]]={}
    links_capacities:dict[tuple[str,...],int]={}

    def add_link(self, zone1: str, zone2: str, capacity: int) -> None:
        self.adjacencies[zone1].add(zone2)
        self.adjacencies[zone2].add(zone1)
        order_tuple = tuple(sorted([zone1, zone2]))
        self.links_capacities[order_tuple] = capacity

    def add_zone(self,zone:Zone,kind:str)->None:
        if kind=="start_hub":
            self.start_hub=zone.name
        elif kind=="end_hub":
            self.end_hub=zone.name
        self.zones[zone.name]=zone
        self.adjacencies[zone.name]=set()

    def get_link_capacity(self,zone1:str,zone2:str)->int:
        order_tuple=tuple(sorted([zone1,zone2]))
        return  self.links_capacities[order_tuple]

    def update_link_capacity(self,zone1:str,zone2:str,amount:int)->None:
        order_tuple=tuple(sorted([zone1,zone2]))
        self.links_capacities[order_tuple]=self.links_capacities[order_tuple] -amount




    
