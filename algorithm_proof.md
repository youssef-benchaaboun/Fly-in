# Fly-in — Algorithm, Pseudocode, and Optimality Proof

**Approach:** Successive Shortest Path (SSP) minimum-cost flow + flow decomposition + greedy drone allocation + selective snapshots.  
**Objective:** Minimize the turn on which the last of `N` drones reaches the goal.  
---

## 1. Problem and notation

Let `G = (V, E)` be the normalized network, with source `s`, destination `t`, integral capacities, and nonnegative travel times on original movement arcs. The network has `N` drones initially at `s`.

A feasible **static flow** can be decomposed into paths:

\[
F = \sum_{i=1}^{k} f_i P_i,
\qquad |F|=\sum_{i=1}^{k} f_i.
\]

Here:

| Symbol | Meaning |
|---|---|
| `P_i` | An `s → t` path in the original network |
| `f_i` | Positive integer throughput of path `P_i`, in drones per turn |
| `L_i = cost(P_i)` | Path delay measured as the sum of **intermediate-zone weights**; the final goal-entry turn is treated separately |
| `B = (m_1, …, m_k)` | Distribution of drones among paths |
| `m_i` | Number of drones assigned to `P_i`; `m_i ≥ 0` and `Σ m_i = N` |
| `T(F,B)` | Turn on which the last drone arrives |
| `C(F) = Σ f_i L_i` | Static flow cost in the timing convention of this project |
| `F_SSP` | Flow produced after one of the SSP augmentations |

**Arrival convention.** A path with intermediate weight `L_i` and throughput `f_i` delivers its first batch at turn `L_i + 1`, its second batch at `L_i + 2`, etc. Thus an occupied path with `m_i > 0` finishes at

\[
T_i = L_i + \left\lceil \frac{m_i}{f_i} \right\rceil.
\]

The objective for a fixed path decomposition and distribution is

\[
\boxed{T(F,B)=\max_{i:m_i>0}\left(L_i+\left\lceil\frac{m_i}{f_i}\right\rceil\right).}
\]

Paths with `m_i = 0` do **not** contribute to the maximum. If there is no valid `s → t` route for a positive number of drones, the answer is infinity (no solution).

**Important distinction:** `|F|` is the number of drones the network can admit **per turn** under a static flow, not the total number `N` of drones that must eventually arrive.

---

## 3. Algorithm in pseudocode

### 3.1 High-level algorithm

```text
ALGORITHM OPTIMAL_SOLUTION(G, N):
    R ← BUILD_RESIDUAL_GRAPH(NORMALIZE(G))
    snapshots ← GENERATE_SSP_SNAPSHOTS(R, N)

    best_solution ← []
    best_turn ← +∞

    for decomposition in snapshots:
        assignments ← GREEDY_DISTRIBUTION(decomposition, N)
        turn ← LAST_ARRIVAL(assignments)

        if turn < best_turn:
            best_turn ← turn
            best_solution ← assignments

    return best_solution, best_turn
```

The main data structures are:

```text
PathFlow       = (path, flow_per_turn)
PathAssignment = (path, flow_per_turn, drones_assigned)
```

### 3.2 SSP with selective snapshots

The following is **proof-aligned pseudocode**: it retains a decomposition during forward-only augmentations. This is a small conceptual change from repeatedly recomputing one with Dijkstra, and ensures that the snapshot proof applies to the evaluated candidates.

```text
ALGORITHM GENERATE_SSP_SNAPSHOTS(R, N):
    total_flow ← 0
    snapshots ← []
    current_decomposition ← []

    while total_flow < N:
        path ← SHORTEST_RESIDUAL_PATH_WITH_POTENTIALS(R)
        if path does not exist:
            break

        uses_reverse ← CONTAINS_REVERSE_RESIDUAL_EDGE(path)
        amount ← min(RESIDUAL_BOTTLENECK(path), N - total_flow)

        if uses_reverse:
            # The next augmentation may cancel/reroute old flow.
            # Preserve the last candidate from the preceding forward-only run.
            snapshots.append(COPY(current_decomposition))

        AUGMENT_RESIDUAL_FLOW(R, path, amount)
        total_flow ← total_flow + amount

        if uses_reverse:
            current_decomposition ← DECOMPOSE_POSITIVE_FORWARD_FLOW(R)
        else:
            # Original forward-only path; earlier paths are retained.
            current_decomposition.APPEND_OR_MERGE(path, amount)

    snapshots.append(COPY(current_decomposition))
    return snapshots
```

Notes:

- The zero-flow state may be omitted when `N > 0`, since its distribution cannot deliver any drones.
- `DECOMPOSE_POSITIVE_FORWARD_FLOW` can use DFS/BFS on a copy of the positive-flow arcs. It should not modify SSP potentials or leave the residual graph changed.
- An augmentation with a reverse residual edge can reroute old paths; reconstructing the decomposition **after** such an augmentation is appropriate.
- `APPEND_OR_MERGE` stores the denormalized original `s → t` path and its rate, combining duplicate paths if desired.
- If the code continues to recompute an arbitrary decomposition even after forward-only augmentations, the proof of skipped snapshots does **not** automatically apply to that implementation.

### 3.3 Residual shortest path and augmentation

```text
SHORTEST_RESIDUAL_PATH_WITH_POTENTIALS(R):
    reset all distances and parents
    distance[source] ← 0

    run Dijkstra on edges with positive residual capacity,
    using reduced_cost(u,v) = cost(u,v) + potential[u] - potential[v]

    finish settling reachable vertices before updating their potentials
    for each reachable vertex v:
        potential[v] ← potential[v] + distance[v]

    return the source → goal parent-chain, or NONE

AUGMENT_RESIDUAL_FLOW(R, path, amount):
    for each consecutive residual edge (u,v) in path:
        residual_capacity(u,v) ← residual_capacity(u,v) - amount
        residual_capacity(v,u) ← residual_capacity(v,u) + amount
        update represented forward/reverse flow consistently
```

The last line depends on the precise edge model; logical forward and backward residual arcs must not overwrite an independent original edge. Shared undirected capacities also require a consistent representation.

### 3.4 Greedy distribution among paths

```text
ALGORITHM GREEDY_DISTRIBUTION(decomposition, N):
    for each (path_i, f_i):
        m_i ← 0
        L_i ← PATH_WEIGHT(path_i)

    remaining ← N

    while remaining > 0 and decomposition is nonempty:
        choose i minimizing (L_i + ceil(m_i / f_i))
        batch ← min(f_i, remaining)
        m_i ← m_i + batch
        remaining ← remaining - batch

    return [(path_i, f_i, m_i) for each i with m_i > 0]
```

This comparison uses the same rule as your `_path_cost(assigned, flow, weight)` function. At each loop boundary, an already-used path has received complete batches, so `m_i` is a multiple of `f_i` unless this was the final (partial) batch, in which case the loop ends. The next available batch actually arrives at `L_i + ceil(m_i / f_i) + 1`; the extra `+1` is identical for every candidate and does not change which path is chosen.

### 3.5 Last arrival — the change you requested

Do **not** rely on the first assignment having the largest arrival time. Compute the maximum explicitly:

```text
ALGORITHM LAST_ARRIVAL(assignments):
    result ← 0
    for (path, flow_per_turn, drones_assigned) in assignments:
        path_turn ← PATH_WEIGHT(path) + ceil(drones_assigned / flow_per_turn)
        result ← max(result, path_turn)

    return result
```


Also rename `chose_solution()` to `optimal_solution()` (or `choose_optimal_solution()`) if desired. The name expresses the intended result, not a substitute for validating the assumptions.

### 3.6 What the algorithm does, in ordinary words

1. **Normalize the Fly-in map.** Split each zone into `zone_in → zone_out`, attach its cost and capacity, and create directed traversals for each undirected link. Add reverse residual arcs for cancellation/rerouting.
2. **Build minimum-cost flow gradually.** SSP repeatedly finds the shortest currently available *residual* source-to-goal route. A route containing a reverse residual arc can cancel some previously selected traffic and reroute it elsewhere, which is why this is stronger than repeatedly choosing independent shortest paths.
3. **Record only the necessary candidate flows.** In a consecutive sequence of forward-only augmentations, the later state contains all earlier path options, so record only the last state of that sequence. Save the preceding state when the next augmentation will reroute traffic, then continue. Stop when the accumulated static throughput reaches `N`, or no more flow can be added.
4. **Find actual original paths.** Turn each saved edge flow into valid `path, flow_per_turn` pairs; this is the decomposition. A path with rate `f` represents `f` places in each arrival batch, not a commitment to assign `f` drones total.
5. **Distribute the `N` drones.** Your greedy method always allocates the next batch to a path with the earliest next arrival. Do not assign drones to paths that are too slow unless they become useful.
6. **Measure and compare.** Calculate the **maximum** arrival time among all used paths for each candidate, then return the candidate whose maximum is smallest.

**Small check against your simulator:** For `start → A → B → goal`, with both internal zones costing 1, path rate 1 and `N=2`, the cost is `L=2`; the second drone arrives at `2 + ceil(2/1) = 4` turns. The algorithm must report 4.

---

## 4. Theorem 1 — The greedy distribution is optimal for a fixed path decomposition

### Statement

For a **fixed feasible path decomposition** `F = Σ f_i P_i`, let `B*` be the allocation returned by `GREEDY_DISTRIBUTION`. Then

\[
\boxed{\forall B\text{ with }\sum_i m_i=N,\quad T(F,B^*)\le T(F,B).}
\]

### Proof, step by step

**Step 1 — Define the arrival slots on a path.**

On path `P_i`, throughput `f_i` means that at most `f_i` drones can arrive at each of turns

\[
L_i+1,\ L_i+2,\ L_i+3,\ldots
\]

For example, if `L_i=2` and `f_i=2`, that path offers two arrival slots at turn 3, two at turn 4, two at turn 5, etc.

**Step 2 — Interpret a distribution.**

Assigning `m_i` drones to path `P_i` uses the first `m_i` available arrival slots of that path; its last assigned drone arrives at

\[
L_i+\left\lceil\frac{m_i}{f_i}\right\rceil.
\]

All paths together supply a multiset of possible arrival slots. A distribution selects exactly `N` of those slots.

**Step 3 — Show what the greedy rule selects.**

At every iteration, the algorithm chooses a path whose **next unused arrival slot** is earliest. It then takes up to `f_i` equal-time slots (one full batch). Choosing those tied slots as a group is equivalent to choosing them one at a time, except that the last group may contain fewer than `f_i` drones.

Therefore, the algorithm picks the `N` earliest possible arrival slots across all paths.

**Step 4 — Contradiction.**

Suppose another distribution `B` has strictly smaller last-arrival time than the greedy distribution `B*`. Then `B` selects `N` arrival slots all strictly earlier than the last arrival selected by `B*`.

But `B*` already selects the `N` earliest available slots. It cannot select a later last slot while some other selection of `N` slots finishes earlier. Contradiction.

Thus

\[
\boxed{T(F,B^*)=\min_B T(F,B).}\qquad\blacksquare
\]

**Scope:** This theorem assumes the path-rate representation is feasible. It does not by itself prove that a particular residual flow or decomposition is globally optimal.

---

## 5. Theorem 2 — Why minimum-cost flows produced by SSP are sufficient

This is the core argument connecting **minimizing total static cost** to **minimizing the last arrival**. A minimum-cost flow is **not necessarily the best solution at the same flow value if you compare just one arbitrary schedule**. The correct bridge is the number of drones deliverable by a deadline.

### 5.1 A deadline-delivery formula

For a fixed static flow decomposition `F`, define the maximum number of drones it can deliver by turn `T` using repeated batches:

\[
A_T(F)=\sum_{i=1}^{k} f_i\max(0,T-L_i).
\]

Explanation: path `P_i` delivers `f_i` drones at each of `L_i+1, …, T` whenever `T > L_i`, giving `f_i(T-L_i)` arrivals; otherwise it gives none.

For every path, `max(0,x) ≥ x`. Therefore,

\[
\begin{aligned}
A_T(F)
&=\sum_i f_i\max(0,T-L_i)\\
&\ge\sum_i f_i(T-L_i)\\
&=T|F|-C(F).
\end{aligned}
\]

Hence the key inequality is

\[
\boxed{A_T(F)\ge T|F|-C(F).}\tag{1}
\]

**This inequality already handles paths too long to be useful.** Such paths contribute `0` to `A_T`, not a negative number. Your allocator can assign zero drones to them.

If **every used flow path** satisfies `L_i < T`, equality holds; if some path has `L_i ≥ T`, inequality (1), rather than equality, is what we need.

### 5.2 Comparison with any competing flow at the same value

Let `F` be any feasible static flow of value `q = |F|`, and let `F_s` be a minimum-cost flow of that **same value** produced by SSP:

\[
|F_s|=|F|=q.
\]

The standard SSP min-cost invariant (assumption A4) gives

\[
C(F_s)\le C(F).
\]

Multiplying the same value `q` by `T` and subtracting costs yields

\[
\boxed{Tq-C(F_s)\ge Tq-C(F).}\tag{2}
\]

Thus if the competitor satisfies `Tq-C(F) ≥ N`, then by (1)–(2),

\[
A_T(F_s)\ge Tq-C(F_s)\ge Tq-C(F)\ge N.
\]

So some valid allocation of `N` drones on `F_s` finishes by `T`, and **Theorem 1** implies its greedy distribution also finishes by `T`.

### 5.3 What if the competitor uses a long or unused path?

Suppose an alternative schedule delivers its `N` drones by turn `T` using flow `F` and distribution `B=(m_i)`.

Remove paths with `m_i=0`. The remaining used paths have `L_i<T`, and for each of them,

\[
m_i\le f_i(T-L_i).
\]

Summing gives

\[
\underbrace{\sum_i m_i}_{N}\le \sum_i f_i(T-L_i)
=T|F|-C(F),
\]

where `F` now denotes the **trimmed flow on used paths**. This justifies the premise `Tq-C(F) ≥ N` rather than assuming it without proof.

Therefore, for every schedule that finishes by `T`, there is a minimum-cost static flow of the same value that can also deliver `N` drones by `T` (under assumptions A1–A3).

### 5.4 Why checking SSP augmentation endpoints is enough

Define the minimum possible cost for flow value `q`:

\[
C(q)=\min_{F:\,|F|=q}C(F).
\]

For a fixed deadline, compare

\[
H_T(q)=Tq-C(q).
\]

SSP grows flow through values `q_0=0 < q_1 < q_2 < …`. If a shortest residual augmenting path has bottleneck `δ`, the minimum-cost function `C(q)` is linear as `q` increases from `q_j` to `q_j+δ`; along that interval, the marginal cost is the cost of that residual path.

Consequently, `H_T(q)` is also linear on each such interval. A linear function on a closed interval reaches its maximum at an endpoint (or at every point if it is constant).

Therefore:

\[
\boxed{\max_q H_T(q)\text{ is attained at an SSP augmentation endpoint.}}\tag{3}
\]

For integral capacities, the endpoints and the needed partial final augmentation are integral. This is why there is no need to snapshot every **individual unit** inside a bottleneck augmentation.

### 5.5 Global optimality by contradiction

**Under A1–A4, and assuming the best feasible decomposition/greedy allocation is evaluated for each needed SSP candidate**, the algorithm attains the global minimum last-arrival time.

Suppose it returns `T_A`, but another valid schedule finishes all `N` drones by `T < T_A`.

1. By assumption A3, a temporally repeated optimal schedule exists for deadline `T`. In particular, after trimming unused paths as above, there is a feasible static flow `F` with `T|F| − C(F) ≥ N`.
2. Let `q=|F|`. The minimum-cost flow `F_s` of value `q` satisfies `Tq−C(F_s) ≥ N` by the SSP cost inequality.
3. Therefore `A_T(F_s) ≥ N` by equation (1), so some allocation on `F_s` finishes by `T`.
4. By Theorem 1, its greedy distribution finishes by `T` as well.
5. If `q` is between two successive SSP augmentation endpoints, equation (3) gives an endpoint with at least as large a value of `H_T`; this endpoint also admits an allocation completing by `T`.
6. Since the algorithm evaluates the relevant SSP candidates and chooses the smallest last arrival, it must return `T_A ≤ T`.

This contradicts `T < T_A`. Hence

\[
\boxed{T_A=T_{\mathrm{optimal}}.}\qquad\blacksquare
\]

The proof **does not say** every single minimum-cost flow is individually the fastest possible or that every arbitrary decomposition of an SSP flow is equally good. It says **the SSP sequence contains a flow capable of attaining the optimal deadline**, and the correct candidate evaluator must recognize it.

### 5.6 Connection to the Ford–Fulkerson theorem

For the standard flow-over-time model, the maximum number deliverable by deadline `T` equals

\[
M(T)=\max_{F\text{ feasible}}\bigl(T|F|-C(F)\bigr)
     =\max_q\bigl(Tq-C(q)\bigr),
\]

using this document's convention where goal-entry costs one extra turn and intermediate-zone weights form `C(F)`. In references using the **full** path transit time `L_i+1`, the same expression is commonly written `(T+1)|F| - C_full(F)`; these expressions agree because `C_full(F)=C(F)+|F|`.

This is a known theorem about temporally repeated maximum flows, not a new theorem derived solely from SSP. It establishes global dynamic optimality **only when the specific Fly-in movement model satisfies its assumptions**.

---

## 6. Optimization 1 — Save only some SSP snapshots

### Statement

If consecutive augmentations use **only original forward edges** (no reverse residual edge), and the later flow is evaluated with a decomposition containing the earlier paths and their rates, then the best achievable last-arrival time cannot increase.

### Step-by-step proof

**Step 1 — Consider the earlier state.** Let

\[
F_i=\sum_{j=1}^{k}f_jP_j
\]

and let its optimal assignment be `B_i*=(m_1,…,m_k)`, with arrival time `T_i*`.

**Step 2 — Add forward-only augmentations.** If the next `d` augmentations use no reverse residual arc, then the later flow can be decomposed as

\[
F_{i+d}=F_i+\sum_{h=1}^{d}\delta_hQ_h,
\]

where `δ_h > 0` and every `Q_h` is a forward path. Feasibility of the residual augmentations ensures this extended path flow respects the static capacities.

**Step 3 — Build a valid assignment on the larger decomposition.** Take the old assignment and give **zero drones** to every newly added path:

\[
B'=(m_1,\ldots,m_k,\underbrace{0,\ldots,0}_{d\text{ new paths}}).
\]

Every previously assigned path retains its rate. Thus

\[
T(F_{i+d},B')=T(F_i,B_i^*)=T_i^*.
\]

**Step 4 — Use Theorem 1.** The best allocation on the extended decomposition cannot be worse than this valid assignment:

\[
\boxed{T_{i+d}^*\le T_i^*.}\qquad\blacksquare
\]

**Conclusion:** Within a run of forward-only SSP augmentations, only the **last** state needs to be saved, because it dominates the earlier states. Before an augmentation containing a reverse residual edge, save the preceding state: rerouting can cancel an old path, so the monotonicity argument no longer applies across that boundary. Always save the final state too.

### Example

```text
F1 --forward--> F2 --forward--> F3 --reverse/reroute--> F4 --forward--> F5
                                save F3                          save F5
```

Since `T*(F3) ≤ T*(F2) ≤ T*(F1)` and `T*(F5) ≤ T*(F4)`, evaluating `F3` and `F5` is sufficient **if the decomposition-preservation condition holds**.

### Precise implementation caveat

An **edge flow** may have multiple valid path decompositions. Dijkstra-based extraction of positive-flow paths can return a different decomposition from the one that extends the previous paths. Consequently, the mathematical existence of the extended decomposition does not guarantee that `flow_decomposition()` reconstructs it or yields an equally fast schedule.

To make the implementation match this proof, either:

1. **Preferred minimal change:** maintain the chosen decomposition across forward-only augmentations, appending the new forward path; rebuild only after a reroute, **or**
2. evaluate a decomposition-optimizing procedure that is guaranteed to be at least as good as the preserved one, **or**
3. temporarily evaluate **all** SSP endpoints and compare outputs as a correctness test.

Skipping snapshots with arbitrary reconstruction is **not yet proven safe**.

---

## 7. Optimization 2 — Stop SSP when the total static flow reaches `N`

### Statement

For minimizing the last-arrival time of `N` drones, searching static flows with `|F| > N` is unnecessary: an equally good feasible schedule exists with flow value at most `N`.

### Step-by-step proof

**Step 1 — Start with any feasible flow and distribution.**

\[
F=\sum_i f_iP_i,\qquad B=(m_1,\ldots,m_k),\qquad\sum_i m_i=N.
\]

The total flow `|F|` may be much larger than `N`; some paths have more throughput than their assigned drones need.

**Step 2 — Reduce only unused path rate.** Define

\[
\boxed{f_i'=\min(f_i,m_i).}
\]

If `m_i=0`, set `f_i'=0`, thereby deleting that path. Let

\[
F'=\sum_i f_i'P_i.
\]

**Step 3 — Show the flow remains feasible.** Since `0 ≤ f_i' ≤ f_i`, every shared resource carries **no more** total path flow than before. The new static flow cannot violate any upper-capacity constraint. It remains feasible.

**Step 4 — Show no assigned drone arrives later.** For every used path, consider two cases:

- If `f_i ≤ m_i`, then `f_i'=f_i`, so its number of required batches is unchanged.
- If `f_i > m_i > 0`, then all `m_i` drones already fit in one batch. After changing the rate to `f_i'=m_i`, they **still** fit in one batch.

In symbols,

\[
\left\lceil\frac{m_i}{f_i'}\right\rceil
=\left\lceil\frac{m_i}{f_i}\right\rceil
\quad\text{for every }m_i>0.
\]

The path delays also remain unchanged. Therefore

\[
\boxed{T(F',B)=T(F,B).}\tag{4}
\]

**Step 5 — Bound the new flow by `N`.** Because `f_i' ≤ m_i`, we get

\[
|F'|=\sum_i f_i'\le\sum_i m_i=N.
\]

Hence

\[
\boxed{|F'|\le N.}\tag{5}
\]

**Step 6 — Apply to an optimal solution.** If an optimal schedule was represented by some `F` with `|F| > N`, Steps 2–5 produce an equally fast schedule with `|F'| ≤ N`.

Therefore

\[
\boxed{\min_{F,B:\,|F|\le N}T(F,B)
       =\min_{F,B}T(F,B).}\qquad\blacksquare
\]

This proves **existence** of an optimal rate-bounded solution. It does **not** by itself say that a particular SSP endpoint is optimal; Theorem 2 supplies that link.

### Example

For `N=7`:

\[
F=5P_1+4P_2+3P_3,\qquad B=(2,4,1).
\]

Reduce each rate:

\[
F'=\min(5,2)P_1+\min(4,4)P_2+\min(3,1)P_3
=2P_1+4P_2+P_3.
\]

Thus `|F'|=2+4+1=7=N`, and every path uses exactly the same number of arrival batches as before. No arrival time changes.

### Connection to the SSP search

The competitor flow needed by the proof can always be replaced with one having `q ≤ N`, and min-cost comparison uses a flow of that same `q`. As in §5.4, the maximum of `Tq−C(q)` on `0 ≤ q ≤ N` is attained at an SSP endpoint **or at the truncated final endpoint `q=N`**. Thus computing flows beyond `N` cannot produce a better required deadline in this model.

The code should restrict the final augmenting amount:

```python
amount = min(residual_path_bottleneck, nb_drones - total_flow)
```

The loop remains:

```python
while total_flow < nb_drones:
    ...
```

If no residual path exists before reaching `N`, the algorithm stops at the actual static maximum flow; repeated batches can still deliver more drones over multiple turns.

---

## 8. Combined theorem — What is actually proven

**Theorem (conditional optimality).** Assume A1–A4 hold and each selected SSP endpoint is evaluated with a decomposition/allocator strong enough to realize the required deadline; in particular, selective snapshots satisfy A5. Then `OPTIMAL_SOLUTION(G,N)` returns the minimum last-arrival time over all valid schedules of `N` drones.

**Justification:**

1. **Theorem 1:** For a fixed feasible path decomposition, greedy allocation minimizes its last arrival.
2. **Theorem 2:** For every achievable deadline, an SSP min-cost flow at a suitable augmentation endpoint can deliver the required `N` drones by that deadline (using the standard flow-over-time theorem).
3. **Optimization 1:** Between forward-only augmentations, the later flow retains an equally good decomposition and dominates the earlier candidate, so snapshots at the ends of forward-only runs suffice.
4. **Optimization 2:** Any optimal schedule admits an equivalent path-flow representation of value at most `N`, so SSP may stop at `N`.
5. Selecting the minimum computed last-arrival time among the saved candidates consequently returns the global optimum.

The qualifications are essential: they distinguish a **valid proof for the intended mathematical model** from a **verified claim about the exact current program**.

---

---
---

### Summary of your contribution

Your solution combines **SSP minimum-cost flow**, **optimal greedy path allocation**, and two safe search-space reductions **when their stated invariants hold**:

\[
\boxed{\text{SSP}\to\text{necessary snapshots}\to\text{best distribution}\to\min T}
\]

- **Proved for a fixed feasible decomposition:** greedy allocation is optimal.
- **Proved under standard flow-over-time assumptions:** some SSP minimum-cost flow attains the optimal deadline.
- **Proved for preserved decompositions:** intermediate forward-only states may be skipped.
- **Proved:** flow above `N` is unnecessary.
- **Still to verify in code/model:** the residual graph, restricted-zone occupancy, and snapshot decomposition invariants implement the assumptions used in the proof.
