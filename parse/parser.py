"""Parse Fly-in map files into the map models."""

import re

from map import StaticMap, Zone


class Parse:
    """Validate map input and build a ``StaticMap``."""

    _ZONE_PATTERN = re.compile(
        r"^(start_hub|end_hub|hub):\s*(\S+)\s+([+-]?\d+)\s*"
        r"([+-]?\d+)(?:\s+(\[.*\]))?$"
    )
    _CONNECTION_PATTERN = re.compile(
        r"^connection:\s+([^\s-]+)-([^\s-]+)(?:\s+(\[.*\]))?$"
    )
    _DRONES_PATTERN = re.compile(r"^nb_drones:\s*(\d+)\s*$")
    _ZONE_TYPES = {"normal", "blocked", "restricted", "priority"}
    _ZONE_METADATA = {"zone", "color", "max_drones"}
    _CONNECTION_METADATA = {"max_link_capacity"}

    def __init__(self) -> None:
        """Initialize source-line tracking for cleaned input."""
        self._line_numbers: list[int] = []

    @staticmethod
    def _parse_number(value: str) -> tuple[int | None, str | None]:
        """Parse a positive integer capacity value."""
        if re.fullmatch(r"[0-9]+", value) is None:
            return None, "the value must contain only decimal digits"
        number = int(value)
        if number <= 0:
            return None, "the number must be positive"
        return number, None

    def read_file(self, file_name: str) -> tuple[list[str] | None, str | None]:
        """Read all lines from a map file, returning an error on failure."""
        try:
            with open(file_name, encoding="utf-8") as file:
                return file.readlines(), None
        except OSError as error:
            return None, f"file problem: {error}"

    def valid_lines(self, lines: list[str]) -> tuple[list[str], list[str]]:
        """Remove comments and blanks while validating line prefixes."""
        clean_lines: list[str] = []
        self._line_numbers = []
        errors: list[str] = []
        allowed_prefix: set[str] = {
            "start_hub",
            "end_hub",
            "hub",
            "connection",
            "nb_drones",
        }

        for number, line in enumerate(lines, start=1):
            if line.lstrip().startswith("#") or not line.lstrip():
                continue
            prefix = line.strip().split(":", 1)[0]
            if prefix not in allowed_prefix:
                errors.append(f"Line {number}: unknown or malformed prefix")
                continue
            clean_lines.append(line.strip())
            self._line_numbers.append(number)

        if not clean_lines:
            return [], ["Input file is empty or contains only comments"]

        return clean_lines, errors

    def _parse_metadata_hub(
        self, block: str, ignore_max_drones: bool = False
    ) -> tuple[dict[str, object] | None, list[str] | None]:
        """Parse optional zone metadata without changing the zone model."""
        errors: list[str] = []
        options: dict[str, object] = {}
        seen_keys: set[str] = set()
        if not block.startswith("[") or not block.endswith("]"):
            return None, ["metadata is not inside []"]
        if not block[1:-1].strip():
            return None, ["metadata block is empty"]

        for token in block[1:-1].split():
            if token.count("=") != 1:
                errors.append("metadata does not respect key=value")
                continue
            key, value = token.split("=", 1)
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
            elif ignore_max_drones:
                continue
            else:
                number, error = self._parse_number(value)
                if error is not None:
                    errors.append(f"key:{key} problem with number: {error}")
                    continue
                options[key] = number
        if errors:
            return None, errors
        return options, None

    def _parse_nb_drones(
        self, first_line: str
    ) -> tuple[int | None, str | None]:
        """Parse the required positive drone count on the first clean line."""
        clean_line = first_line.lstrip()
        match = self._DRONES_PATTERN.fullmatch(clean_line)
        if match is None:
            message = (
                f"Line {self._line_numbers[0]}: first line must be "
                "'nb_drones: <positive_integer>'"
            )
            return None, message
        number = int(match.group(1))
        if number <= 0:
            return None, (
                f"Line {self._line_numbers[0]}: nb_drones must be positive"
            )
        return number, None

    def _parse_conection(
        self,
        line: str,
        line_number: int,
        zones: dict[str, Zone]
    ) -> tuple[str, str, int | None, list[str] | None]:
        """Parse one connection declaration and its capacity."""
        errors: list[str] = []
        match = self._CONNECTION_PATTERN.fullmatch(line)
        if match is None:
            return "", "", None, [
                f"Line {line_number}: invalid connection; expected "
                "'connection: <name>-<name> [metadata]'"
            ]
        name1, name2, block = match.groups()
        if name1 not in zones:
            errors.append(
                f"Line {line_number}: zone '{name1}' must be defined before "
                "the connection"
            )
        if name2 not in zones:
            errors.append(
                f"Line {line_number}: zone '{name2}' must be defined before "
                "the connection"
            )
        if block is None:
            return name1, name2, None, errors or None
        token = block[1:-1].strip()
        if not token:
            errors.append(f"Line {line_number}: metadata block is empty")
            return "", "", None, errors
        if token.count("=") != 1:
            errors.append(
                f"Line {line_number}: metadata must respect key=value"
            )
            return "", "", None, errors
        key, value = token.split("=", 1)
        if key not in self._CONNECTION_METADATA:
            errors.append(f"Line {line_number}: unknown metadata key '{key}'")
        if not value:
            errors.append(
                f"Line {line_number}: key '{key}' has an empty value"
            )
            number = None
        else:
            number, error = self._parse_number(value)
            if error is not None:
                errors.append(
                    f"Line {line_number}: key '{key}' has invalid capacity: "
                    f"{error}"
                )
        if errors:
            return "", "", None, errors
        return name1, name2, number, None

    def _parse_zone(
        self,
        line: str,
        line_number: int,
        seen_names: set[str],
        seen_coordinates: set[tuple[int, int]],
    ) -> tuple[str, Zone | None, list[str] | None]:
        """Parse one start, end, or regular zone declaration."""
        match = self._ZONE_PATTERN.fullmatch(line)
        if match is None:
            return (
                "not",
                None,
                [
                    f"Line {line_number}: invalid zone; expected "
                    "'<type>: <name> <x> <y> [metadata]'"
                ],
            )
        kind, name, x_text, y_text, block = match.groups()
        errors: list[str] = []
        if "-" in name:
            errors.append(
                f"Line {line_number}: zone names cannot contain dashes"
            )
        if name in seen_names:
            errors.append(f"Line {line_number}: duplicate zone name '{name}'")

        coordinate: tuple[int, int] = (int(x_text), int(y_text))
        if coordinate in seen_coordinates:
            errors.append(f"Line {line_number}: duplicate zone coordinate '{name}'")        

        options: dict[str, object] = {}
        if block is not None:
            parsed_options, problem = self._parse_metadata_hub(
                block,
                ignore_max_drones=kind in {"start_hub", "end_hub"},
            )
            if problem is not None:
                errors.extend(
                    f"Line {line_number}: {message}" for message in problem
                )
            elif parsed_options is not None:
                options = parsed_options
        if errors:
            return kind, None, errors

        max_drones = options.get("max_drones", 1)
        zone_type = options.get("zone", "normal")
        color = options.get("color")
        if not isinstance(max_drones, int):
            return kind, None, [f"Line {line_number}: invalid max_drones"]
        if not isinstance(zone_type, str):
            return kind, None, [f"Line {line_number}: invalid zone type"]
        if color is not None and not isinstance(color, str):
            return kind, None, [f"Line {line_number}: invalid color"]
        new_zone = Zone(
            name=name,
            coordinate=coordinate,
            color=color,
            zone_type=zone_type,
            max_drones=max_drones,
            neighbours={},
        )
        return kind, new_zone, None

    def parse_map(
        self, lines: list[str]
    ) -> tuple[StaticMap | None, list[str] | None]:
        """Validate cleaned input and construct the existing map model."""
        errors: list[str] = []
        zones: dict[str, Zone] = {}
        zone_line_numbers: dict[str, int] = {}
        seen_names: set[str] = set()
        seen_coordinates: set[tuple[int, int]] = set()
        start_hub: Zone | None = None
        end_hub: Zone | None = None
        allowed_zone: set[str] = {"start_hub", "end_hub", "hub"}
        clean_lines, problems = self.valid_lines(lines)
        errors.extend(problems)
        if not clean_lines:
            return None, errors

        number_drones, drone_error = self._parse_nb_drones(clean_lines[0])
        if drone_error is not None:
            errors.append(drone_error)
        numbered_lines = zip(clean_lines, self._line_numbers)
        for index, (line, line_number) in enumerate(numbered_lines):
            prefix = line.split(":", 1)[0].lstrip()
            if prefix == "nb_drones":
                if index != 0:
                    errors.append(
                        f"Line {line_number}: unexpected duplicate "
                        "nb_drones declaration"
                    )
                continue
            if prefix not in allowed_zone:
                continue
            kind, zone, zone_errors = self._parse_zone(
                line=line,
                line_number=line_number,
                seen_names=seen_names,
                seen_coordinates=seen_coordinates,
            )
            if zone_errors is not None:
                errors.extend(zone_errors)
                continue
            if zone is None:
                errors.append(f"Line {line_number}: zone could not be parsed")
                continue
            seen_names.add(zone.name)
            seen_coordinates.add(zone.coordinate)
            if kind == "start_hub":
                if start_hub is not None:
                    errors.append(f"Line {line_number}: duplicate start_hub")
                else:
                    start_hub = zone
                    zones[zone.name] = zone
                    zone_line_numbers[zone.name] = line_number
            elif kind == "end_hub":
                if end_hub is not None:
                    errors.append(f"Line {line_number}: duplicate end_hub")
                else:
                    end_hub = zone
                    zones[zone.name] = zone
                    zone_line_numbers[zone.name] = line_number
            elif kind == "hub":
                zones[zone.name] = zone
                zone_line_numbers[zone.name] = line_number

        if start_hub is None:
            errors.append("Input: missing start_hub")
        if end_hub is None:
            errors.append("Input: missing end_hub")

        for line, line_number in zip(clean_lines, self._line_numbers):
            prefix = line.split(":", 1)[0].lstrip()
            if prefix != "connection":
                continue
            previously_defined = {
                name: zone
                for name, zone in zones.items()
                if zone_line_numbers[name] < line_number
            }
            name1, name2, link_capacity, er = self._parse_conection(
                line=line,
                line_number=line_number,
                zones=previously_defined,
            )
            if link_capacity is None:
                link_capacity = 1
            if er:
                errors.extend(er)
                continue
            if name1 == name2:
                errors.append(
                    f"Line {line_number}: connection cannot link a zone "
                    "to itself"
                )
                continue
            if (
                name2 in zones[name1].neighbours
                or name1 in zones[name2].neighbours
            ):
                errors.append(f"Line {line_number}: duplicate connection")
                continue
            zones[name1].neighbours[name2] = link_capacity
            zones[name2].neighbours[name1] = link_capacity
        if errors:
            return None, errors
        if number_drones is None or start_hub is None or end_hub is None:
            return None, ["Input: map construction failed"]
        static_map = StaticMap(
            nb_drones=number_drones,
            hubs=zones,
            start_hub=start_hub,
            end_hub=end_hub,
        )
        return static_map, None
