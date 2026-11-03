# Parsing Design Review and Improvements

## Rating

**Current design: 6.5/10.** The parser has a solid beginner-to-intermediate
structure: grammar, metadata, models, and file I/O are separated enough to follow.
The score is limited by state mutation during validation, the two-pass ordering bug,
missing exact-hub enforcement, and the absence of automated tests and clean linting.

## How to make it more professional

1. **Separate syntax, semantics, and construction.** First turn a line into a typed record, then validate cross-line rules, then construct the final network.
2. **Prefer immutable parsed data.** Capacities in a parsed map describe limits; runtime “remaining capacity” belongs in simulation state, not in `Zone` or `Network` mutation methods.
3. **Use `dataclass` and enums.** `ZoneType(Enum)` prevents magic strings, and standard dataclasses remove an unnecessary dependency for plain data containers.
4. **Model unlimited capacity clearly.** Use `int | None` or a dedicated property for start/end instead of storing a misleading finite integer.
5. **Return a result object.** A `ParseResult(network: Network | None, errors: list[ParseError])` makes success/failure explicit and prevents consumers using partial state.
6. **Centralize grammar constants.** Consistent whitespace and comment normalization should happen once before prefix-specific parsing.
7. **Avoid broad mutable parser state.** Local sets and counters make repeated calls safe and make each function easier to test independently.
8. **Use precise names and messages.** `_parse_connection`, `zone_metadata`, and “duplicate nb_drones declaration” reduce explanation time during peer review.
9. **Add unit tests before pathfinding.** Parsing is the trust boundary; table-driven pytest cases will make later algorithm debugging much easier.
10. **Meet repository requirements now.** Add `Makefile`, dependency declaration, `.gitignore`, README, and ensure `flake8` plus the required `mypy` command pass continuously.

## Strong target architecture

```text
MapReader (I/O only)
  -> LineLexer (comments/prefix/metadata tokens)
  -> MapParser (typed declarations in source order)
  -> MapValidator (cross-line subject rules)
  -> NetworkBuilder (creates immutable static graph)
```

This is more structure than the current project strictly needs, so it can remain four
small classes/modules. The important professional qualities are deterministic behavior,
no partial output on failure, explicit invariants, and a regression test for every rule.

