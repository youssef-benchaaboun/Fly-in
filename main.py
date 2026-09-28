import sys

from parsed import Parse


def main() -> None:
    arguments = sys.argv[1:]
    if len(arguments) != 1:
        print("usage: python3 main.py <map_file>")
        return
    if not arguments[0]:
        print("map filename cannot be empty")
        return

    parser = Parse()
    lines, file_error = parser.read_file(arguments[0])
    if file_error is not None:
        print(file_error)
        return
    if lines is None:
        print("could not read map file")
        return

    static_map, errors = parser.verifier_values(lines)
    if errors:
        for error in errors:
            print(error)
        return
    if static_map is not None:
        print(static_map.print_hubs())


if __name__ == "__main__":
    main()
