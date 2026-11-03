import re
from models import Network, Zone


class Parse:

    _ZONE_PATTERN = re.compile(
        r"^(start_hub|end_hub|hub)\s*:\s*(\S+)\s+([+-]?\d+)\s*"
        r"([+-]?\d+)(?:\s+(\[.*\]))?$"
    )
    _CONNECTION_PATTERN = re.compile(
        r"^connection:\s+([^\s-]+)-([^\s-]+)(?:\s+(\[.*\]))?$"
    )
    _DRONES_PATTERN = re.compile(r"^nb_drones\s*:\s*(\d+)\s*$")
    _ZONE_TYPES = {"normal", "blocked", "restricted", "priority"}
    _ZONE_METADATA = {"zone", "color", "max_drones"}
    _CONNECTION_METADATA = {"max_link_capacity"}

    def __init__(self) -> None:
        self._line_numbers: list[int] = []
        self.seen_coordinates:list[tuple[int,int]]=[]
        self.seen_names:list[str]=[]
        self.network=Network()

    @staticmethod
    def _parse_number(value: str) -> tuple[int, str]:
        if re.fullmatch(r"[0-9]+", value) is None:
            return 0, "the value must contain only decimal digits"
        number = int(value)
        if number <= 0:
            return 0, "the number must be positive"
        return number,""

    
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
        allowed_prefix: set[str] = {"start_hub","end_hub","hub","connection","nb_drones",}
        for number, line in enumerate(lines, start=1):
            if line.strip().startswith("#") or not line.strip():
                continue
            prefix = line.strip().split(":", 1)[0].strip()
            if prefix not in allowed_prefix:
                errors.append(f"Line {number}: unknown or malformed prefix")
                continue
            if("#" in line):
                clean_lines.append(line.split("#")[0].rstrip())
            else:
                clean_lines.append(line.rstrip())
            self._line_numbers.append(number)

        if not clean_lines and not errors:
            return [], ["Input file is empty or contains only comments"]

        return clean_lines, errors

    def _parse_nb_drones(self, first_line: str) -> str:
        clean_line = first_line.strip()
        match = self._DRONES_PATTERN.fullmatch(clean_line)
        if match is None:
            message = (
                f"Line {self._line_numbers[0]}: first line must be "
                "'nb_drones: <positive_integer>'"
            )
            return message
        number = int(match.group(1))
        if number <= 0:
            return f"Line {self._line_numbers[0]}: nb_drones must be positive"
        self.network.nb_drones=number
        return ""

    def _parse_metadata_hub(self, block: str,ignore:bool) -> tuple[dict[str, str], list[str]]:
        errors: list[str] = []
        options: dict[str, str] = {}
        seen_keys: set[str] = set()
        if not block.startswith("[") or not block.endswith("]"):
            return {}, ["metadata is not inside []"]
        if not block[1:-1].strip():
            return {}, ["metadata block is empty"]

        for token in block[1:-1].split():
            if token.count("=") != 1:
                errors.append("metadata does not respect key=value")
                continue
            key, value = token.split("=",1)
            if key not in self._ZONE_METADATA:
                errors.append(f"key:{key} does not belong to the keys")
                continue
            if key in seen_keys:
                errors.append(f"key:{key} is duplicated")
                continue
            seen_keys.add(key)
            if not value:
                errors.append(f"key:{key} has an empty value")
                continue
            if key == "color":
                options[key] = value
            elif key == "zone":
                if value not in self._ZONE_TYPES:
                    errors.append(f"key:{key} has bad value {value}")
                    continue
                options[key] = value
            elif ignore==False:
                number, error = self._parse_number(value)
                if error !="" or number==0:
                    errors.append(f"key:{key} problem with number: {error}")
                    continue
                options[key] = str(number)
        if errors:
            return {}, errors
        return options, []
    
    def _parse_zone(self,line: str,line_number: int) -> list[str]:
        match = self._ZONE_PATTERN.fullmatch(line)
        if match is None:
            return [f"Line {line_number}: invalid zone; expected "'<type>: <name> <x> <y> [metadata]'""]
        kind, name, x_text, y_text, block = match.groups()
        errors: list[str] = []
        if "-" in name:
            errors.append(
                f"Line {line_number}: zone names cannot contain dashes"
            )
        if name in self.seen_names:
            errors.append(f"Line {line_number}: duplicate zone name '{name}'")

        coordinate: tuple[int, int] = (int(x_text), int(y_text))

        options: dict[str, str] = {}
        if block:
            ignore=(kind=="start_hub" or kind=="end_hub")
            options, problem = self._parse_metadata_hub(block,ignore=ignore)
            if problem !=[]:
                errors.extend(f"Line {line_number}: {message}" for message in problem)

        if kind=="start_hub" and self.network.start_hub is not None:
            errors.append(f"Line {line_number}: duplicate start_hub")
        if kind=="end_hub" and self.network.end_hub is not None:
            errors.append(f"Line {line_number}: duplicate end_hub")

        if errors:
            return errors

        self.seen_names.append(name)
        self.seen_coordinates.append(coordinate)
        
        max_drones = int(options.get("max_drones", "1"))
        zone_type = options.get("zone", "normal")
        color = options.get("color")
        new_zone = Zone(
            name=name,
            coordinate=coordinate,
            color=color,
            zone_type=zone_type,
            max_drones=max_drones
        )
        self.network.add_zone(new_zone,kind)
        return []

    def _parse_conection(self,line: str,line_number: int) -> list[str]:
        errors: list[str] = []
        match = self._CONNECTION_PATTERN.fullmatch(line)
        if match is None:
            return [f"Line {line_number}: invalid connection; expected ""'connection: <name>-<name> [metadata]'"]
        name1, name2, block = match.groups()
        if name1==name2:
             errors.append(f"Line {line_number}: connection cannot link a zone to itself")

        if name1 not in self.network.zones:
            errors.append(
                f"Line {line_number}: zone '{name1}' must be defined before "
                "the connection"
            )

        if name2 not in self.network.zones:
            errors.append(
                f"Line {line_number}: zone '{name2}' must be defined before "
                "the connection"
            )
        else:
            if (name1 in self.network.adjacencies[name2]):
                errors.append(f"Line {line_number}: duplicate connection")


        if block is None:
            if errors:
                return errors
            self.network.add_link(name2,name1,1)
            return []
        
        token = block[1:-1].strip()
        if not token:
            errors.append(f"Line {line_number}: metadata block is empty")
            return errors
        if token.count("=") != 1:
            errors.append(
                f"Line {line_number}: metadata must respect key=value"
            )
            return errors
        key, value = token.split("=", 1)
        if key not in self._CONNECTION_METADATA:
            errors.append(f"Line {line_number}: unknown metadata key '{key}'")
        if not value:
            errors.append(
                f"Line {line_number}: key '{key}' has an empty value"
            )
            return errors
        number, error = self._parse_number(value)
        if error !="" or number ==0:
            errors.append(f"Line {line_number}: key '{key}' has invalid capacity: "f"{error}")
        if errors:
            return errors
        self.network.add_link(name1,name2,number)
        return []

    def parse_map(self, lines: list[str]) ->list[str]:
            errors: list[str] = []
            clean_lines, problems = self.valid_lines(lines)
            errors.extend(problems)
            if not clean_lines:
                return errors
            drone_error = self._parse_nb_drones(clean_lines[0])
            if drone_error != "":
                errors.append(drone_error)
            numbered_lines = zip(clean_lines, self._line_numbers)
            for index, (line, line_number) in enumerate(numbered_lines):
                prefix = line.split(":", 1)[0].strip()
                if prefix == "nb_drones":
                    if index != 0:
                        errors.append(
                            f"Line {line_number}: duplicate or misplaced "
                            "nb_drones declaration"
                        )
                    continue
                if prefix =="connection":
                    errors_connection = self._parse_conection(line=line,line_number=line_number)
                    if errors_connection:
                        errors.extend(errors_connection)
                    continue
                zone_errors = self._parse_zone(line=line,line_number=line_number)
                if zone_errors is not None:
                    errors.extend(zone_errors)

            if self.network.start_hub is None:
                errors.append("Input: missing start_hub")
            if self.network.end_hub is None:
                errors.append("Input: missing end_hub")
    
            if errors:
                return errors
            return[]
