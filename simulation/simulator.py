import time
class Simulator:
    def __init__(self,solution:list[tuple[list[str],int,int]]):
        self.solution:list[tuple[list[str],int,int]]=solution
    
    def simulation(self)->None:
        all_arrived:bool=True
        nb_drones=[0]*len(self.solution)
        groups:list[list[list[str]]]=[]
        curent_postion:dict[tuple[str,...],str]={}
        assiment_numbers=1
        turn=1
        while(True):
            for i in range(len(self.solution)):
                path,flow,nb_path=self.solution[i]
                if nb_drones[i]<nb_path:
                    amount=min(flow,nb_path-nb_drones[i])
                    nb_drones[i] +=amount
                    group:list[str]=[]
                    for id in range(assiment_numbers,assiment_numbers+amount):
                        group.append(f"D{id}")
                    if len(groups)<=i:
                        groups.append([])
                    if group not in groups[i]:
                        groups[i].append(group)
                    assiment_numbers+=amount
                for gp in groups[i]:
                    if tuple(gp) not in curent_postion:
                        postion=path[1]
                        curent_postion[tuple(gp)]=postion
                    else:
                        if curent_postion[tuple(gp)]=="-":
                            continue
                        inedx=path.index(curent_postion[tuple(gp)])+1
                        if inedx >=len(path):
                            curent_postion[tuple(gp)]="-"
                        else:
                            curent_postion[tuple(gp)]=path[inedx]
            all_arrived =all(pos == "-" for pos in curent_postion.values())
            if all_arrived:
                break
            print(f"Turn{turn}:",end="")
            loop=True
            j=0
            while loop:
                i=0
                loop=False
                while(i<len(groups)):
                    if j>=len(groups[i]):
                        i+=1
                        continue
                    dgp=groups[i][j]
                    for drone in dgp:
                        if curent_postion[tuple(dgp)]=="-":
                            continue
                        print(f"{drone}-{curent_postion[tuple(dgp)]}   ",end="")
                    loop=True
                    i+=1
                if loop==True:
                    j+=1
            turn +=1
            print()
                
                


