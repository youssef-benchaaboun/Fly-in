"""Command-line entry point for Fly-in."""

import sys

from Algorithms import Alogrithm
from parse import Parse
from simulation import Simulator


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
    errors = parser.parse_map(lines=lines)
    if errors:
        for error in errors:
            print(error)
        return
    algo = Alogrithm(parser.network)
    decomposition = algo.flow_decomapstion()
    solution = algo.min_arrive_time(decomposition)
    sim = Simulator(solution, parser.network)
    sim.simulation()


if __name__ == "__main__":
    main()
