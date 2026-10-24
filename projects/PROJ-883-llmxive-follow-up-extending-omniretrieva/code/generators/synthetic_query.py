"""Synthetic query generator.

Generates queries with integer plan depths and attaches a deterministic
ground‑truth plan using :class:`ReferenceEngine`.  The public API matches
the expectations of the unit tests in ``tests/unit/test_synthetic_query.py``.
"""
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import List, Dict, Any

from llmxive_toolkit import get_logger, paths
from .reference_engine import ReferenceEngine

log = get_logger(__name__)

# The maximum depth we support for synthetic generation.  If a caller
# requests a larger depth we cap it and emit a warning.
MAX_DEPTH = 4


class SyntheticQueryGenerator:
    """Generate synthetic queries with integer depth."""

    def __init__(
        self,
        seed: int = 42,
        levels: List[int] | None = None,
        count_per_level: int = 5,
    ) -> None:
        """
        Parameters
        ----------
        seed: int
            Random seed for reproducibility.
        levels: List[int] | None
            Desired plan depths.  If ``None`` the default ``[1, 2, 3, 4]`` is used.
        count_per_level: int
            Number of queries to generate for each depth level when using
            :meth:`generate`.  This value is ignored by
            :meth:`generate_queries` which accepts an explicit ``count``
            argument.
        """
        self.seed = seed
        self.complexity_levels = levels if levels is not None else [1, 2, 3, 4]
        self.count_per_level = count_per_level
        self.rng = random.Random(seed)
        self.engine = ReferenceEngine()
        log.debug(
            "SyntheticQueryGenerator initialized with seed=%s, levels=%s",
            seed,
            self.complexity_levels,
        )

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------
    def _effective_level(self, level: int) -> int:
        """Return a depth that does not exceed ``MAX_DEPTH``; log if capped."""
        if level > MAX_DEPTH:
            log.warning(
                "Requested depth %d exceeds maximum %d – capping to %d",
                level,
                MAX_DEPTH,
                MAX_DEPTH,
            )
            return MAX_DEPTH
        return level

    def _generate_query_structure(self, level: int) -> Dict[str, Any]:
        """Create a minimal structure describing a synthetic query."""
        eff = self._effective_level(level)
        ops = ["filter"]
        if eff >= 3:
            ops.append("join")
        if eff == MAX_DEPTH:
            ops.append("recursive_lookup")
        structure = {
            "target_depth": eff,
            "operations": ops,
            "nodes": [{"id": i} for i in range(eff + 1)],
            "edges": [{"source": i, "target": i + 1} for i in range(eff)],
        }
        log.debug("Generated query structure for level %d: %s", level, structure)
        return structure

    # ------------------------------------------------------------------
    # Public generation API
    # ------------------------------------------------------------------
    def generate(self) -> List[Dict[str, Any]]:
        """Create queries using the per‑level ``count_per_level`` setting."""
        queries: List[Dict[str, Any]] = []
        for level in self.complexity_levels:
            eff_level = self._effective_level(level)
            for _ in range(self.count_per_level):
                q = self._create_query(eff_level)
                queries.append(q)
        return queries

    def generate_queries(self, count: int) -> List[Dict[str, Any]]:
        """Generate *count* queries distributed evenly across the configured levels."""
        if count <= 0:
            raise ValueError("count must be a positive integer")

        num_levels = len(self.complexity_levels)
        base = count // num_levels
        remainder = count % num_levels

        queries: List[Dict[str, Any]] = []
        for idx, level in enumerate(self.complexity_levels):
            num = base + (1 if idx < remainder else 0)
            for _ in range(num):
                queries.append(self._create_query(level))
        log.debug(
            "Generated %d queries (requested %d) across levels %s",
            len(queries),
            count,
            self.complexity_levels,
        )
        return queries

    def _create_query(self, level: int) -> Dict[str, Any]:
        """Create a single query dictionary for *level*."""
        eff_level = self._effective_level(level)
        qid = f"q_{eff_level}_{self.rng.randint(0, 1_000_000)}"

        # Build a realistic logical plan based on the synthetic structure.
        structure = self._generate_query_structure(level)
        logical_steps = structure["operations"]

        # Build step objects for the reference engine.
        step_objs = [
            {"step_id": s, "estimated_cost": 1.0} for s in logical_steps
        ]

        # Generate a deterministic plan identifier.
        plan_id = self.engine.generate_plan(
            {"query_id": qid, "steps": step_objs}
        )

        query: Dict[str, Any] = {
            "query_id": qid,
            "source_type": self.rng.choice(["text", "relational", "graph"]),
            "complexity_level": int(eff_level),
            "logical_plan": {"steps": logical_steps},
            "ground_truth_plan": {
                "steps": logical_steps,
                "plan_id": plan_id,
                "estimated_depth": int(eff_level),
            },
            # Preserve the raw identifier for downstream components.
            "ground_truth_plan_id": plan_id,
        }
        return query

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------
    def save_queries(self, filepath: Path | str, count: int = 10) -> None:
        """Write *count* generated queries to *filepath* as JSON."""
        path = Path(filepath) if not isinstance(filepath, Path) else filepath
        queries = self.generate_queries(count)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(queries, f, indent=2)
        log.info("Saved %d synthetic queries to %s", len(queries), path)

    # Alias kept for backward compatibility with older scripts.
    write_to_file = save_queries
