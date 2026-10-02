import re
from map import  StaticMap, Zone


class Parse:
    _ZONE_PATTERN = re.compile(
        r"^(start_hub|end_hub|hub):\s*+(\S+)\s+([+-]?\d+)\s*+"
        r"([+-]?\d+)(?:\s+(\[.*\]))?$"
    )
    _CONNECTION_PATTERN = re.compile(
        r"^connection:\s+([^\s-]+)-([^\s-]+)(?:\s+(\[.*\]))?$"
    )
    _DRONES_PATTERN = re.compile(r"^nb_drones:\s* + \d+$")
    _ZONE_TYPES = {"normal", "blocked", "restricted", "priority"}
    _ZONE_METADATA = {"zone", "color", "max_drones"}
    _CONNECTION_METADATA = {"max_link_capacity"}
    _ZONE_COLOR={"red","white","yelleow","green"}

    def __init__(self) -> None:
        self._line_numbers: list[int] = []

    def _parse_number(s:str)->tuple[int|None,str|None]:
        try:
            val=int(s.lstrip())
        except ValueError as e:
            return None,e
        if val < 0:
            return None,"the number is negative"
        return val,None
    
    def read_file(self, file_name: str) -> tuple[list[str] | None, str | None]:
        try:
            with open(file_name, encoding="utf-8") as file:
                return file.readlines(), None
        except OSError as error:
            return None, f"file problem: {error}"

    def valid_lines(self, lines: list[str]) -> tuple[list[str], list[str]]:
        clean_lines: list[str] = []
        self._line_numbers = []
        errors: list[str] = []
        allowed_prefix:set[str]={"start_hub", "end_hub", "hub", "connection","nb_drones"}

        for number, line in enumerate(lines, start=1):
            if line.lstrip().startswith('#') or not line.lstrip():
                 continue
            prefix = line.split(":", 1)[0]
            if prefix not in allowed_prefix:
                errors.append(f"Line {number}: unknown or malformed prefix")
                continue
            if line.count(":") != 1:
                errors.append(f"Line {number}: unknown or malformed prefix")
                continue
            clean_lines.append(line)
            self._line_numbers.append(number)

        if not clean_lines:
            return [], ["Input file is empty or contains only comments"]

        return clean_lines, errors

    def _parse_metadata_hub(self,block:str)->tuple[dict|None,str]:
        options={}        
        if not block.startswith("[") or not block.endswith("]"):
            return None,"meta data not inside []"
        
        block=block[1:-1]
        list_value=block.split()
        for val in list_value:
            if val.count("=")!=1:
                return None,"meta data doesnt respek key=value"
            key,value=val.split("=")
            key=key.lstrip()
            value=value.lstrip()
            if key not in self._ZONE_METADATA :
                return None,f"key:{key} doesnt belong to the keys"
            if key in options:
                return None,"key:{key} is duplicated"
            if key.lower()=="color":
                if value not in self._ZONE_COLOR:
                    options[key]=None
                options[key]=val
            elif key.lower()=="zone":
                if value not in self._ZONE_TYPES:
                    return None,f"key :{key} has bad value {value}"
                options[key]=value
            elif key.lower()=="max_drones":
                nm,er=self._parse_number(value)
                if er:
                    return None,f"key:{key} problem with number{er}"
                options[key]=nm
            
                
    def _parse_nb_drones(self,first_line:str)->tuple[int|None,str|None]:
        clean_line=first_line.lstrip()
        if self._DRONES_PATTERN.fullmatch(clean_line) is None:
            message =f"Line {self._line_numbers[0]}: first line must be ""'nb_drones: <positive_integer>'"
            return None,message
        number:str=clean_line.split(":")[1].lstrip()
        return int(number),None
    
    def _parse_zone(self,line:str,line_number:str,zones:dict[str,Zone],cordes:list[tuple(int,int)])->tuple[str,Zone|None,list[str]|None]:
        match = self._ZONE_PATTERN.fullmatch(line)
        if match is None:
            return "not", None,[f"Line {line_number}: invalid zone; expected ""'<type>: <name> <x> <y> [metadata]'"]
        kind, name, x_text, y_text, block = match.groups()
        errors: list[str] = []
        if "-" in name:
            errors.append(
                f"Line {line_number}: zone names cannot contain dashes"
            )
        if name in zones:
            errors.append(f"Line {line_number}: duplicate zone name '{name}'")

        cord:tuple=(int(x_text),int(y_text))
        if cord in cordes:
            errors.append(f"Line {line_number}: duplicate coordinate '{cord}'")
        if block:
            option,problem=self._parse_metadata_hub(block)
            if not option:
                errors.append(problem)
        else:
            option:dict={}
        if errors:
            return kind,None,errors
        max_drones=option.get("max_drones",1)
        zone_type=option.get("zone_type","normal")
        color=option.get("color",None)
        new_zone=Zone(
                         name=name
                         ,coordinate=cord
                         ,color=color
                         ,zone_type=zone_type
                         ,max_drones=max_drones
                         ,neighbours={})
        return kind,new_zone,None

    def parse_map(self,lines:list[str])->tuple[StaticMap|None ,list[str]| None]:
        errors=[]
        zones:dict[str,Zone]={}
        count_start=0
        count_end=0
        cordes:list[tuple[int,int]]=[]
        allowed_zone:set[str]={"start_hub", "end_hub", "hub"}
        clean_lines,problems=self.valid_lines(lines)
        if problems:
            errors.extend(problems)
        if not clean_lines:
            return None,errors
        number_drones,er=self._parse_nb_drones(clean_lines[0])
        if er:
            errors.append(er)
        for line ,number_line in zip(clean_lines,self._line_numbers):
            if line.split(":")[0].lstrip() in allowed_zone:
                kind,zone,err=self._parse_zone(line=line,line_number=number_line,zones=zones,cordes=cordes)
                if err:
                    errors.extend(err)
                    continue
                if kind =="start_hub":
                    start_hub=zone
                    count_start+=1
                elif kind =="end_hub":
                    end_hub=zone
                    count_end+=1 
                elif kind=="hub":
                    zones[zone.name]=zone
        if count_start !=1:
            errors.append("not unique start")
        if count_end !=1:
            errors.append("not unique end")
        if errors :
            return None,errors
        else:
            stac=staticmethod(number_line=number_drones
                              ,hubs=zones
                              ,start_hub=start_hub
                              ,end_hub=end_hub
            )
            return stac,None


