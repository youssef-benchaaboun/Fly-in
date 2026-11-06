from models import Network,Zone
import math


class Alogrithm:

    def __init__(self,network:Network):
        self.network=network
        self.zones=self.network.zones
        self.adjacencies=self.network.adjacencies
        self.link_capacity=self.network.links_capacities

    def allowed_hubs(self)->list[Zone]:
        hubs:list[Zone]=[]
        for zone in self.zones.values():
            if zone.zone_type =="blocked" or zone.get_zone_capacity() <=0:
                continue
            hubs.append(zone)
        return hubs
    
    def priority_counter(self,curent:Zone)->int:
        i=0
        while(True):
            if curent.zone_type=="priority":
                i+=1
            if curent.parent is None:
                break
            curent=self.zones[str(curent.parent)]
        return i
    
    def constucte_min(self,hubs:list[Zone])->Zone:
        min_dist=min([zone.distance for zone in hubs])
        candidate=[zone for zone in hubs if zone.distance==min_dist]
        max_priority=max([self.priority_counter(zone) for zone in candidate])
        best_candidate=[zone for zone in candidate if self.priority_counter(zone)==max_priority]
        return best_candidate[0]

    def relaxtion(self,curent:str)->None:
        nieghbours=[ng for ng in self.adjacencies[curent] if self.zones[ng].zone_type!="blocked" and self.network.get_link_capacity(curent,ng)>0]
        for ng in nieghbours:
            condition=self.zones[ng].distance>self.zones[curent].distance +self.zones[ng].get_zone_wieght()
            if condition:
                self.zones[ng].parent=curent
                self.zones[ng].distance=self.zones[curent].distance +self.zones[ng].get_zone_wieght()

    def singal_source_shortest_path(self)->list[str]:
        self.network.intialize()
        hubs=self.allowed_hubs()
        while(hubs):
            curent_procces=self.constucte_min(hubs)
            self.relaxtion(curent_procces.name)
            hubs.remove(curent_procces)

        curent=self.network.end_hub
        path=[]
        while(curent):
            zone=self.zones[curent]
            path.append(curent)
            curent=zone.parent
        path.reverse()
        if len(path)<=1:
            return []
        return path

    def get_path_wight(self,path:list[str])->int:
        wight=0
        for zone in path:
            wight += self.zones[zone].get_zone_wieght()
        return wight
    def get_path_flow(self,path:list[str])->int:
        candadite=[]
        for i in range(len(path)-1):
            candadite.append(self.network.get_link_capacity(path[i],path[i+1]))
            if path[i] in (self.network.start_hub,self.network.end_hub):
                continue
            candadite.append(self.zones[path[i]].get_zone_capacity())
        if len(candadite) <=0:
            return 0
        return min(candadite)

    def update_path_flow(self,path:list[str])->None:
        flow=self.get_path_flow(path=path)
        for i in range(len(path)-1):
            self.network.update_link_capacity(path[i],path[i+1],flow)
            self.zones[path[i]].update_zone_capacity(amount=flow)

    def max_netework_flow_decomapstion(self)->list[tuple[list[str],int]]:
        decomapstion=[]
        while(self.singal_source_shortest_path()):
            path=self.singal_source_shortest_path()
            flow=self.get_path_flow(path)
            decomapstion.append((path,flow))
            self.update_path_flow(path=path)

        return decomapstion

    def min_arrive_time(self,decompastion:list[tuple[list[str],int]])->tuple[list[list[str]],list[int],list[int]]:
        nb_drones=self.network.nb_drones
        wieght=[]
        drones_path=[]
        paths=[]
        flows:list[int]=[]
        for solution in decompastion:
            path,flow=solution
            wieght.append(self.get_path_wight(path))
            drones_path.append(0)
            paths.append(path)
            flows.append(flow)
        assined=0
        print(wieght)
        while(assined<nb_drones):
            cost=2*nb_drones + nb_drones -1
            j=0
            for i in range(len(paths)):
                path_cost=math.ceil(drones_path[i]/flows[i])-1 + wieght[i]
                if cost > path_cost:
                    j=i
                    cost=path_cost
            drones_path[j] += min(flows[j],nb_drones-assined)
            assined =assined+min(flows[j],nb_drones-assined)
            

        return (paths,flows,drones_path)


