*This project has been created as part of the 42 curriculum by yben-cha.*

# Fly-in

## Description

Fly-in routes a fleet of drones from a start hub to an end hub through a
capacity-constrained network. It parses and validates a map, finds available
paths, allocates drones to minimize their arrival time, and prints every move
as a coloured terminal simulation.

## Algorithm and implementation

The implementation uses successive shortest path (SSP) minimum-cost flow,
positive-flow decomposition, greedy drone allocation, and selective snapshots.
It does not use a graph library.

First, every usable zone is split into an `in -> out` edge. That edge carries
the zone capacity and its movement cost: one for normal and priority zones and
two for restricted zones. Start and end capacities are set to the drone count.
Each bidirectional connection becomes two directed traversal edges with its
declared capacity. Blocked zones are omitted.

The pathfinder repeatedly runs a Dijkstra-style search on positive-capacity
residual edges. Reduced costs and vertex potentials allow reverse residual
edges to cancel and reroute earlier flow while keeping shortest-path searches
valid. Equal-distance candidates prefer the parent chain containing more
priority zones. An augmentation sends the path bottleneck, limited by the
number of drones still required.

Forward-only augmentations preserve all earlier path choices, so only the last
state in such a run needs evaluation. Before a residual reroute, the preceding
decomposition is saved. After rerouting, BFS decomposes the positive forward
flow into original start-to-end paths without modifying the residual flow.
The final decomposition is always saved.

The allocation stage repeatedly assigns up to one path-flow batch to the path
with the earliest next arrival. For a path of intermediate-zone weight `L`,
throughput `f`, and `m` assigned drones, its last arrival is
`L + ceil(m / f)`. The candidate result is the maximum of this value across
all used paths, and the best saved SSP candidate is selected.

### Why the allocation is optimal

A path with weight `L` and flow `f` offers `f` arrival slots at turn `L + 1`,
another `f` at `L + 2`, and so on. Choosing the path with the earliest next
batch therefore selects the globally earliest available arrival slots. If a
different allocation finished sooner, it would need to select `N` slots
earlier than the `N` earliest slots, which is impossible. Thus the greedy
allocation minimizes the last arrival for a fixed decomposition.

For a static flow `F` with value `|F|`, path rates `f_i`, path weights `L_i`,
and cost `C(F) = sum(f_i * L_i)`, the number deliverable by deadline `T` is:

```text
A_T(F) = sum(f_i * max(0, T - L_i)) >= T * |F| - C(F)
```

SSP produces a minimum-cost flow at each augmentation endpoint. For a fixed
deadline, `T * q - C(q)` is linear between consecutive endpoints, so its
maximum occurs at an endpoint. Consequently, evaluating the proof-preserving
SSP candidates and applying the optimal greedy allocation finds the minimum
last-arrival turn under the static-flow-over-time assumptions used by Fly-in.
The complete assumptions, endpoint argument, and selective-snapshot proof are
available in [algorithm_proof.md](algorithm_proof.md).

With the current list-based Dijkstra implementation, one shortest-path search
costs `O(V^2 + E)`. For `A` augmentations, routing costs
`O(A * (V^2 + E))`; decomposition costs `O(V + E)` per rebuilt snapshot, and
allocation is proportional to the number of emitted path batches. Graph and
residual storage use `O(V + E)` memory, in addition to saved decompositions.

## Visual representation

Restricted movements take exactly two turns. The first output names the
connection (`D1-source-restricted`); the following turn names the restricted
zone (`D1-restricted`). Zone colours are rendered with ANSI terminal escapes.
Common terminal colour names are supported and any unrecognized or omitted
colour safely falls back to white. One output line represents one simultaneous
turn, making parallel movement, waiting, and restricted-zone transit visible.

## Instructions

Python 3.10 or newer is required.

```sh
make install
make run
```

Run static validation with:

```sh
make lint
```

Other mandatory convenience targets are `make debug` and `make clean`.
`make lint-strict` runs the subject-recommended strict mypy check.

To run another supplied map:

```sh
make run maps/hard/03_ultimate_challenge.txt
```

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

## Benchmark results

The implementation reaches the exact subject v3.1 target on every supplied
map:

| Map | Drones | Turns | Subject optimum |
|---|---:|---:|---:|
| Linear path | 2 | 4 | 4 |
| Simple fork | 4 | 4 | 4 |
| Basic capacity | 4 | 4 | 4 |
| Dead end trap | 5 | 8 | 8 |
| Circular loop | 6 | 10 | 10 |
| Priority puzzle | 5 | 6 | 6 |
| Maze nightmare | 8 | 13 | 13 |
| Capacity hell | 12 | 16 | 16 |
| Ultimate challenge | 15 | 26 | 26 |
| The Impossible Dream | 25 | 43 | 43 |

## Resources

- [Python documentation](https://docs.python.org/3/)
- [Dijkstra's algorithm](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm)
- [Minimum-cost flow](https://en.wikipedia.org/wiki/Minimum-cost_flow_problem)
- [Ford-Fulkerson algorithm](https://en.wikipedia.org/wiki/Ford%E2%80%93Fulkerson_algorithm)
- [ANSI escape codes](https://en.wikipedia.org/wiki/ANSI_escape_code)
- The Fly-in version 3.1 subject supplied with the project.

AI was used to review the parser and routing implementation and document the wrok and the proof .
