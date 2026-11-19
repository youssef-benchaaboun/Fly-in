
"""Residual graph for Fly-in min-cost max-flow."""

from dataclasses import dataclass, field
from .normalize_map import MapNormalized


@dataclass
class ResidualGraph(MapNormalized):
    residual_capacity: dict[tuple[str, str], int] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        super().__post_init__()
        self.create_residual_edges()

    def add_capacity(self, src: str, dst: str, capacity: int) -> None:
        key = (src, dst)
        if self.links_type[key] == "residual":
            self.residual_capacity[key] = capacity
        else:
            super().add_capacity(src, dst, capacity)

    def get_capacity(self, src: str, dst: str) -> int:
        key = (src, dst)
        if self.links_type[key] == "residual":
            return self.residual_capacity[key]
        return super().get_capacity(src, dst)

    def update_capacity(self, src: str, dst: str, amount: int) -> None:
        key = (src, dst)
        if self.links_type[key] == "residual":
            remaining = self.residual_capacity[key] - amount
            self.residual_capacity[key] = remaining
        else:
            super().update_capacity(src, dst, amount)

    def create_residual_edges(self) -> None:
        """Create one reverse residual edge per forward edge."""
        original_edges = list(self.links_cost.items())
        for (src, dst), cost in original_edges:
            self.add_edge(
                dst,
                src,
                0,
                -cost,
                "residual",
            )

    def augment_edge(self, src: str, dst: str, amount: int) -> None:
        """Push flow or cancel existing flow."""
        key = (src, dst)
        reverse = (dst, src)
        self.update_capacity(src, dst, amount)
        self.update_capacity(dst, src, -amount)
        self.links_flow[reverse] -= amount
        self.links_flow[key] += amount
