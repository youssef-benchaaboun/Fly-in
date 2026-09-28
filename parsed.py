from map import StaticMap,Zone
from pydantic import ValidationError
import re

class Parse:

    starthub =r"^start_hub:\s+(\S+)\s+(\S+)\s+(\S+)(?:\s)?$"
    endhub=r"^end_hub:\s+(\S+)\s+(\S+)\s+(\S+)(?:\s)?$"
    hub=r"^hub:\s+(\S+)\s+(\S+)\s+(\S+)(?:\s)?$"



    def read_file(self,file_name:str)->tuple[list[str]|None,str|None]:
        try:
            with open(file_name) as file:
                result=file.readlines()
                return (result,None)
        except OSError as error:
            return(None,f"file promplem:{error}")
    
    def valid_lines(self,lines:list[str])->tuple[list[str],list[str]]:
        i=0
        errors:list[str]=[]
        clean_lines:list[str]=[]

        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                clean_lines.append(stripped)

        if not clean_lines:
            return None, ["Input file is empty or contains only comments"]

        first_line = clean_lines[0]
        if not first_line.startswith("nb_drones:"):
            errors.append("first line is not : nb_drones: <number>")
        else:
            try:
                _, value = first_line.split(":", 1)
                if int(value.strip()) <= 0:
                    errors.append("nb_drones must be a positive integer")
            except ValueError:
                errors.append("first line is not : nb_drones: <number>")

        
        allowed_prefixes=("start_hub","end_hub","hub","connection")
        count_start=0
        count_end=0

        for index,line in enumerate(clean_lines[1:],start=2):
            if line.startswith("start_hub"):
                count_start+=1
            elif line.startswith("end_hub"):
                count_end+=1
            if not any(line.startswith(f"{prefix}:") for prefix in allowed_prefixes):
                errors.append(f"Line {index}: invalid prefix structure -> '{line}'")
                continue
            try:
                parts = line.split(":", 1)
                if len(parts) != 2 or not parts[1].strip():
                    errors.append(f"Line {index}: bad line configuration -> '{line}'")
            except Exception:
                errors.append(f"Line {index}: bad line")

        if count_start != 1:
            errors.append(f"Map validation failed: must have exactly 1 start_hub, found {count_start}")
        if count_end != 1:
            errors.append(f"Map validation failed: must have exactly 1 end_hub, found {count_end}")

        return clean_lines, errors

    def verfier_values(self,lines:str)->tuple[StaticMap|None,list[str]]:
        nb_drones:int
        start_hub:Zone
        end_hub:Zone
        hubs:dict[str,Zone]
        clean_lines,errors=self.valid_lines(lines)
        allowed_prefixes=("start_hub","end_hub","hub","connection")
        for line in clean_lines:
            if line.startwith("nb_drones"):
                try:
                    nb_drones =int(line.split(":")[1])
                    if nb_drones <=0:
                        raise ValueError("nb_drones should be positive integer >= 1")
                except ValueError as wrong:
                    errors.append(wrong)
            elif line.startwith("start_hub"):
                match1 = re.match(self.starthub, line)
                if not match1:
                    errors.append("start doesnt respect formula  start_hub: <name> <x> <y> [metadata]")
                    continue
                name, x, y = match1.groups()
                if name in hubs :
                    errors.append("start has name already token")
                    continue
                if "-" in name:
                    errors.append(" connection syntax forbids dashes in zone names.")
                    continue
                #parrse the metadata 
                try:
                    start_hub=Zone(name=name,coordinate=(x,y)) #later metadate
                except ValidationError as e:
                    error_list = [f"{w['loc'][0]}: {w['msg']}" for w in e.errors()]
                    errors.extend(error_list)
                    continue
                hubs.append(start_hub)
            elif line.startwith("end_hub"):
                match1 = re.match(self.endhub, line)
                if not match1:
                    errors.append("end doesnt respect formula  start_hub: <name> <x> <y> [metadata]")
                    continue
                name, x, y = match1.groups()
                if name in hubs :
                    errors.append("end has name already token")
                    continue
                if "-" in name:
                    errors.append(" connection syntax forbids dashes in zone names.")
                    continue
                #parrse the metadata 
                try:
                    end_hub=Zone(name=name,coordinate=(x,y)) #later metadate
                except ValidationError as e:
                    error_list = [f"{w['loc'][0]}: {w['msg']}" for w in e.errors()]
                    errors.extend(error_list)
                    continue
                hubs.append(end_hub)
            elif line.startwith("hub"):
                match1 = re.match(self.endhub, line)
                if not match1:
                    errors.append("hub doesnt respect formula  hub: <name> <x> <y> [metadata]")
                    continue
                name, x, y = match1.groups()
                if name in hubs :
                    errors.append("hub has name already token")
                    continue
                if "-" in name:
                    errors.append(" connection syntax forbids dashes in zone names.")
                    continue
                #parrse the metadata 
                try:
                    hub1=Zone(name=name,coordinate=(x,y)) #later metadate
                except ValidationError as e:
                    error_list = [f"{w['loc'][0]}: {w['msg']}" for w in e.errors()]
                    errors.extend(error_list)
                    continue
                hubs.append(hub1)
        if errors:
            return None,errors
        return(staticmethod(nb_drones,start_hub,end_hub,hubs),[])