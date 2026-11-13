*This project has been created as part of the 42 curriculum by yben-cha.*

# Fly-in

## Description

Fly-in routes a fleet of drones from a start hub to an end hub through a
capacity-constrained network. It parses and validates a map, finds available
paths, allocates drones to minimize their arrival time, and prints every move
as a coloured terminal simulation.

## Algorithm and implementation

The pathfinder repeatedly applies a Dijkstra-style shortest-path search to the
residual network. Blocked zones and exhausted links are excluded. Entering a
restricted zone has weight two, and priority zones break equal-distance ties.
Each discovered path is assigned the minimum residual zone/link capacity along
that path, then those capacities are consumed to produce disjoint flow paths.

The allocation stage repeatedly assigns up to one path-flow batch to the path
with the lowest projected arrival cost. The simulator starts those batches in
parallel and advances each active group once per turn.

Restricted movements take exactly two turns. The first output names the
connection (`D1-source-restricted`); the following turn names the restricted
zone (`D1-restricted`). Zone colours are rendered with ANSI terminal escapes.
Common terminal colour names are supported and any unrecognized or omitted
colour safely falls back to white.

## Instructions

Python 3.10 or newer is required.

```sh
make install
make run MAP=test.txt
```

Run static validation with:

```sh
make lint
```

Other mandatory convenience targets are `make debug` and `make clean`.

## Input example

```text
nb_drones: 1
start_hub: start 0 0
hub: tunnel 1 0 [zone=restricted color=blue]
end_hub: goal 2 0
connection: start-tunnel
connection: tunnel-goal
```

## Expected output

The terminal displays these tokens in colour (ANSI escapes are omitted here):

```text
D1-start-tunnel
D1-tunnel
D1-goal
```

Each line is one turn and each token is one drone movement. Multiple movements
on a turn are separated by spaces.

## Resources

- [Python documentation](https://docs.python.org/3/)
- [Dijkstra's algorithm](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm)
- [ANSI escape codes](https://en.wikipedia.org/wiki/ANSI_escape_code)
- The Fly-in version 1.6 subject supplied with the project.

AI was used to help refactor the minimum-arrival allocation and simulator into
small documented methods, implement restricted-zone and terminal-colour output,
and check the repository with flake8 and mypy. The routing strategy and its
selection logic remain the project's original algorithm.
