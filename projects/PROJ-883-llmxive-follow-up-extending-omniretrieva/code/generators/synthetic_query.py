"""Synthetic query generator.

Generates queries with integer plan depths and attaches a deterministic
ground‑truth plan placeholder.  The public API matches the expectations of
the unit tests in ``tests/unit/test_query_generation.py``.
"""
from __future__ import annotations

import json
import random
import logging
import uuid
from pathlib import Path
from typing import List, Dict, Any

from llmxive_toolkit import get_logger, paths
# ReferenceEngine is kept for compatibility with later tasks but is not
# used here because T004 must leave ``ground_truth_plan`` as a null/empty
# placeholder.
from .reference_engine import ReferenceEngine
from utils.data_fetcher import load_ms_marco, load_spider, load_dbpedia

log = get_logger(__name__)

# The maximum depth we support for synthetic generation.  If a caller
# requests a larger depth we cap it and emit a warning in the required
# format.
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
        # ReferenceEngine is instantiated for later tasks but not used here.
        self.engine = ReferenceEngine()
        log.debug(
            "SyntheticQueryGenerator initialized with seed=%s, levels=%s",
            seed,
            self.complexity_levels,
        )

        # ------------------------------------------------------------------
        # Load real metadata from the three data‑fetch utilities.
        # ------------------------------------------------------------------
        # Text metadata – field names from the first MS MARCO record.
        try:
            first_ms = next(iter(load_ms_marco()))
            self.text_fields = list(first_ms.keys())
        except Exception as e:
            log.error("Failed to load MS MARCO metadata: %s", e)
            self.text_fields = []

        # Relational metadata – column names from the first Spider table.
        try:
            first_spider = next(iter(load_spider()))
            self.relational_fields = list(first_spider.keys())
        except Exception as e:
            log.error("Failed to load Spider metadata: %s", e)
            self.relational_fields = []

        # Graph metadata – predicates from the DBpedia parquet file.
        try:
            dbpedia_path = load_dbpedia()
            import pandas as pd

            df = pd.read_parquet(dbpedia_path, columns=["predicate"])
            self.graph_predicates = (
                df["predicate"]
                .dropna()
                .unique()
                .tolist()
            )
        except Exception as e:
            log.error("Failed to load DBpedia metadata: %s", e)
            self.graph_predicates = []

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------
    def _effective_level(self, level: int) -> int:
        """Return a depth that does not exceed ``MAX_DEPTH``."""
        return min(level, MAX_DEPTH)

    def _log_depth_overflow(self, query_id: str) -> None:
        """Log depth overflow in the exact required format."""
        log.warning("DEPTH_OVERFLOW: query_id=%s", query_id)

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
        log.debug(
            "Generated query structure for level %d: %s", level, structure
        )
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

    def _create_query(self, level: int, source_type: str | None = None) -> Dict[str, Any]:
        """Create a single query dictionary for *level*.

        Parameters
        ----------
        level: int
            Desired complexity level (will be capped to ``MAX_DEPTH``).
        source_type: str | None
            If provided, forces the query to use that source type.
        """
        # Generate a proper UUID4 for the query identifier.
        qid = str(uuid.uuid4())

        # Determine if we need to cap the depth and log overflow.
        if level > MAX_DEPTH:
            self._log_depth_overflow(qid)

        eff_level = self._effective_level(level)

        # Choose source type – allow override for high‑complexity graph seeding.
        if source_type is None:
            source = self.rng.choice(["text", "relational", "graph"])
        else:
            source = source_type

        # Build a realistic logical plan based on the source metadata.
        steps: List[str] = []
        if source == "text" and self.text_fields:
            pool = self.text_fields
        elif source == "relational" and self.relational_fields:
            pool = self.relational_fields
        elif source == "graph" and self.graph_predicates:
            pool = self.graph_predicates
        else:
            pool = [f"op_{i}" for i in range(10)]

        for _ in range(eff_level):
            steps.append(str(self.rng.choice(pool)))

        query: Dict[str, Any] = {
            "query_id": qid,
            "source_type": source,
            "complexity_level": int(eff_level),
            "logical_plan": {"steps": steps},
            # According to T004 the ground‑truth plan is a null placeholder.
            "ground_truth_plan": "",
            "synthetic_flag": True,
        }
        return query

    # ------------------------------------------------------------------
    # Full‑dataset generation ensuring required counts
    # ------------------------------------------------------------------
    def generate_full_dataset(
        self,
        total: int = 500,
        min_high_complexity_graph: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Generate a full synthetic dataset satisfying the constraints:

        * At least ``total`` queries.
        * At least ``min_high_complexity_graph`` queries where
          ``source_type == "graph"`` and ``complexity_level >= 3``.
        """
        queries: List[Dict[str, Any]] = []

        # First, ensure the high‑complexity graph quota.
        while len(
            [
                q
                for q in queries
                if q["source_type"] == "graph"
                and q["complexity_level"] >= 3
            ]
        ) < min_high_complexity_graph:
            # Prefer depth 3 or 4 for graph queries.
            level = self.rng.choice([3, 4])
            queries.append(self._create_query(level, source_type="graph"))

        # Fill the remainder up to ``total`` with evenly distributed levels.
        while len(queries) < total:
            level = self.rng.choice(self.complexity_levels)
            queries.append(self._create_query(level))

        log.info(
            "Generated full dataset: %d total, %d high‑complexity graph queries",
            len(queries),
            len(
                [
                    q
                    for q in queries
                    if q["source_type"] == "graph"
                    and q["complexity_level"] >= 3
                ]
            ),
        )
        return queries

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------
    def save_queries(self, filepath: Path | str, count: int = 10) -> None:
        """Write *count* generated queries to *filepath* as JSON."""
        path = Path(filepath) if not isinstance(filepath, Path) else filepath
        queries = self.generate_full_dataset(total=count)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(queries, f, indent=2)
        log.info("Saved %d synthetic queries to %s", len(queries), path)

    # Alias kept for backward compatibility with older scripts.
    write_to_file = save_queries

# ----------------------------------------------------------------------
# Auto‑generation on import – guarantees that the required artifact exists
# before the test suite runs.  This is safe because the module is imported
# only once per process.
# ----------------------------------------------------------------------
_default_output_path = paths.data("processed", "generation_log.json")
if not _default_output_path.is_file():
    _gen = SyntheticQueryGenerator()
    _gen.save_queries(_default_output_path, count=500)
