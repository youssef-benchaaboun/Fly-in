import re

from map import Connection, StaticMap, Zone


class Parse:
    _ZONE_PATTERN = re.compile(
        r"^(start_hub|end_hub|hub):\s+(\S+)\s+([+-]?\d+)\s+"
        r"([+-]?\d+)(?:\s+(\[.*\]))?$"
    )
    _CONNECTION_PATTERN = re.compile(
        r"^connection:\s+([^\s-]+)-([^\s-]+)(?:\s+(\[.*\]))?$"
    )
    _DRONES_PATTERN = re.compile(r"^nb_drones:\s+(\d+)$")
    _ZONE_TYPES = {"normal", "blocked", "restricted", "priority"}
    _ZONE_METADATA = {"zone", "color", "max_drones"}
    _CONNECTION_METADATA = {"max_link_capacity"}

    def __init__(self) -> None:
        self._line_numbers: list[int] = []

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

        for number, line in enumerate(lines, start=1):
            content = line.split("#", 1)[0].strip()
            if content:
                clean_lines.append(content)
                self._line_numbers.append(number)

        if not clean_lines:
            return [], ["Input file is empty or contains only comments"]

        if self._DRONES_PATTERN.fullmatch(clean_lines[0]) is None:
            errors.append(
                f"Line {self._line_numbers[0]}: first line must be "
                "'nb_drones: <positive_integer>'"
            )
        elif int(clean_lines[0].split(":", 1)[1]) < 1:
            errors.append(
                f"Line {self._line_numbers[0]}: nb_drones must be positive"
            )

        for index, line in enumerate(clean_lines[1:], start=1):
            number = self._line_numbers[index]
            prefix = line.split(":", 1)[0]
            if prefix not in {"start_hub", "end_hub", "hub", "connection"}:
                errors.append(f"Line {number}: unknown or malformed prefix")

        return clean_lines, errors

    @staticmethod
    def _metadata(
        block: str | None, allowed: set[str], line_number: int
    ) -> tuple[dict[str, str], list[str]]:
        if block is None:
            return {}, []
        if not (block.startswith("[") and block.endswith("]")):
            return {}, [f"Line {line_number}: malformed metadata block"]

        content = block[1:-1].strip()
        if not content:
            return {}, [f"Line {line_number}: empty metadata block"]
        result: dict[str, str] = {}
        errors: list[str] = []
        for item in content.split():
            if re.fullmatch(r"[^=\[\]]+=[^=\[\]]+", item) is None:
                errors.append(
                    f"Line {line_number}: malformed metadata tag '{item}'"
                )
                continue
            key, value = item.split("=", 1)
            if not key or not value:
                errors.append(
                    f"Line {line_number}: malformed metadata tag '{item}'"
                )
            elif key not in allowed:
                errors.append(
                    f"Line {line_number}: unknown metadata key '{key}'"
                )
            elif key in result:
                errors.append(
                    f"Line {line_number}: duplicate metadata key '{key}'"
                )
            else:
                result[key] = value
        return result, errors

    @staticmethod
    def _positive_capacity(
        metadata: dict[str, str], key: str, line_number: int
    ) -> tuple[int, list[str]]:
        raw_value = metadata.get(key, "1")
        try:
            value = int(raw_value)
        except ValueError:
            return 1, [f"Line {line_number}: {key} must be a positive integer"]
        if value < 1:
            return 1, [f"Line {line_number}: {key} must be a positive integer"]
        return value, []

    def _parse_zone(
        self, line: str, line_number: int, zones: dict[str, Zone]
    ) -> tuple[str | None, Zone | None, list[str]]:
        match = self._ZONE_PATTERN.fullmatch(line)
        if match is None:
            return None, None, [
                f"Line {line_number}: invalid zone; expected "
                "'<type>: <name> <x> <y> [metadata]'"
            ]
        kind, name, x_text, y_text, block = match.groups()
        errors: list[str] = []
        if "-" in name:
            errors.append(
                f"Line {line_number}: zone names cannot contain dashes"
            )
        if name in zones:
            errors.append(f"Line {line_number}: duplicate zone name '{name}'")

        metadata, metadata_errors = self._metadata(
            block, self._ZONE_METADATA, line_number
        )
        errors.extend(metadata_errors)
        zone_type = metadata.get("zone", "normal")
        if zone_type not in self._ZONE_TYPES:
            errors.append(
                f"Line {line_number}: invalid zone type '{zone_type}'"
            )
        max_drones, capacity_errors = self._positive_capacity(
            metadata, "max_drones", line_number
        )
        if kind in {"start_hub", "end_hub"}:
            max_drones = 1  # The value is valid metadata but has no effect.
            capacity_errors = []
        errors.extend(capacity_errors)
        if errors:
            return kind, None, errors
        return kind, Zone(
            name=name,
            coordinate=(int(x_text), int(y_text)),
            color=metadata.get("color"),
            zone_type=zone_type,
            max_drones=max_drones,
        ), []

    def _parse_connection(
        self, line: str, line_number: int, zones: dict[str, Zone],
        seen: set[frozenset[str]]
    ) -> tuple[Connection | None, list[str]]:
        match = self._CONNECTION_PATTERN.fullmatch(line)
        if match is None:
            return None, [
                f"Line {line_number}: invalid connection; expected "
                "'connection: <zone1>-<zone2> [metadata]'"
            ]
        first, second, block = match.groups()
        errors: list[str] = []
        for name in (first, second):
            if name not in zones:
                errors.append(
                    f"Line {line_number}: connection references undefined "
                    f"zone '{name}'"
                )
        pair = frozenset((first, second))
        if first == second:
            errors.append(
                f"Line {line_number}: self-connections are not allowed"
            )
        elif pair in seen:
            errors.append(f"Line {line_number}: duplicate connection")
        metadata, metadata_errors = self._metadata(
            block, self._CONNECTION_METADATA, line_number
        )
        errors.extend(metadata_errors)
        capacity, capacity_errors = self._positive_capacity(
            metadata, "max_link_capacity", line_number
        )
        errors.extend(capacity_errors)
        if errors:
            return None, errors
        seen.add(pair)
        zones[first].neighbours.append(zones[second])
        zones[second].neighbours.append(zones[first])
        return Connection((first, second), capacity), []

    def verifier_values(
        self, lines: list[str]
    ) -> tuple[StaticMap | None, list[str]]:
        clean_lines, errors = self.valid_lines(lines)
        if not clean_lines:
            return None, errors

        drones_match = self._DRONES_PATTERN.fullmatch(clean_lines[0])
        nb_drones = int(drones_match.group(1)) if drones_match else 0
        zones: dict[str, Zone] = {}
        starts: list[Zone] = []
        ends: list[Zone] = []
        links: list[Connection] = []
        seen_connections: set[frozenset[str]] = set()

        for index, line in enumerate(clean_lines[1:], start=1):
            line_number = self._line_numbers[index]
            if line.startswith("connection:"):
                connection, found = self._parse_connection(
                    line, line_number, zones, seen_connections
                )
                errors.extend(found)
                if connection is not None:
                    links.append(connection)
            elif line.split(":", 1)[0] in {"start_hub", "end_hub", "hub"}:
                kind, zone, found = self._parse_zone(line, line_number, zones)
                errors.extend(found)
                if zone is not None:
                    zones[zone.name] = zone
                    if kind == "start_hub":
                        starts.append(zone)
                    elif kind == "end_hub":
                        ends.append(zone)

        if len(starts) != 1:
            errors.append(
                "Map validation failed: expected exactly 1 start_hub, "
                f"found {len(starts)}"
            )
        if len(ends) != 1:
            errors.append(
                "Map validation failed: expected exactly 1 end_hub, "
                f"found {len(ends)}"
            )
        if errors:
            return None, errors
        return StaticMap(
            nb_drones=nb_drones,
            start_hub=starts[0],
            end_hub=ends[0],
            hubs=list(zones.values()),
            links=links,
        ), []

    def verfier_values(
        self, lines: list[str]
    ) -> tuple[StaticMap | None, list[str]]:
        return self.verifier_values(lines)
