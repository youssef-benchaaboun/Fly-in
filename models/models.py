from dataclasses import dataclass, field
#hhgit@github.com:youssef-benchaaboun/Fly-in.git
@dataclass
class Zone:

    coordinate: tuple[int, int]
    name: str
    color: str | None
    zone_type: str
    max_drones: int | None
    parent:str|None=None
    distance:int=0

    def get_zone_capacity(self) -> int:
        if self.max_drones is None:
            return 1
        return self.max_drones

    def update_zone_capacity(self, amount: int) -> None:
        if self.max_drones is not None:
            self.max_drones -= amount

    def get_zone_wieght(self)->int:
        if self.zone_type=="restricted":
            return 2
        return 1


@dataclass
class Network:

    nb_drones: int = 0
    start_hub: str | None = None
    end_hub: str | None = None
    zones: dict[str, Zone] = field(default_factory=dict)
    adjacencies: dict[str, set[str]] = field(default_factory=dict)
    links_capacities: dict[tuple[str, ...], int] = field(default_factory=dict)

    def add_link(self, zone1: str, zone2: str, capacity: int) -> None:
        self.adjacencies[zone1].add(zone2)
        self.adjacencies[zone2].add(zone1)
        order_tuple = tuple(sorted([zone1, zone2]))
        self.links_capacities[order_tuple] = capacity

    def add_zone(self,zone:Zone,kind:str)->None:
        if kind=="start_hub":
            self.start_hub=zone.name
            zone.max_drones = None
        elif kind=="end_hub":
            self.end_hub=zone.name
            zone.max_drones = None
        self.zones[zone.name]=zone
        self.adjacencies[zone.name]=set()

    def get_link_capacity(self,zone1:str,zone2:str)->int:
        order_tuple=tuple(sorted([zone1,zone2]))
        return  self.links_capacities[order_tuple]

    def update_link_capacity(self,zone1:str,zone2:str,amount:int)->None:
        order_tuple=tuple(sorted([zone1,zone2]))
        self.links_capacities[order_tuple]=self.links_capacities[order_tuple] -amount
        
    def intialize(self)->None:
        for zone in self.zones.values():
            zone.parent=None
            if zone.name==self.start_hub:
                zone.distance=0
            else:
                zone.distance= 2*len(self.zones) + 1



    
