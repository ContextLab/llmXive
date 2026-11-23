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
from utils.data_fetcher import load_ms_marco, load_spider, load_dbpedia

log = get_logger(__name__)

# The maximum depth we support for synthetic generation.
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
            :meth:`generate`.
        """
        self.seed = seed
        self.complexity_levels = levels if levels is not None else [1, 2, 3, 4]
        self.count_per_level = count_per_level
        self.rng = random.Random(seed)
        log.debug(
            "SyntheticQueryGenerator initialized with seed=%s, levels=%s",
            seed,
            self.complexity_levels,
        )

        # ------------------------------------------------------------------
        # Load real metadata from the three data‑fetch utilities.
        # We remove try-except fallbacks to ensure the system fails loudly
        # if real metadata is unavailable, as required by the spec.
        # ------------------------------------------------------------------
        # Text metadata – field names from the first MS MARCO record.
        first_ms = next(iter(load_ms_marco()))
        self.text_fields = list(first_ms.keys())

        # Relational metadata – column names from the first Spider table.
        first_spider = next(iter(load_spider()))
        self.relational_fields = list(first_spider.keys())

        # Graph metadata – predicates from the DBpedia parquet file.
        dbpedia_path = load_dbpedia()
        import pandas as pd
        df = pd.read_parquet(dbpedia_path, columns=["predicate"])
        self.graph_predicates = (
            df["predicate"]
            .dropna()
            .unique()
            .tolist()
        )

    def _effective_level(self, level: int) -> int:
        """Return a depth that does not exceed ``MAX_DEPTH``."""
        return min(level, MAX_DEPTH)

    def _log_depth_overflow(self, query_id: str) -> None:
        """Log depth overflow in the exact required format."""
        log.warning("DEPTH_OVERFLOW: query_id=%s", query_id)

    def _create_query(self, level: int, source_type: str | None = None) -> Dict[str, Any]:
        """Create a single query dictionary for *level*."""
        qid = str(uuid.uuid4())

        if level > MAX_DEPTH:
            self._log_depth_overflow(qid)

        eff_level = self._effective_level(level)

        if source_type is None:
            source = self.rng.choice(["text", "relational", "graph"])
        else:
            source = source_type

        # Build logical plan based on the source metadata.
        if source == "text":
            pool = self.text_fields
        elif source == "relational":
            pool = self.relational_fields
        elif source == "graph":
            pool = self.graph_predicates
        else:
            raise ValueError(f"Unsupported source type: {source}")

        steps: List[str] = []
        for _ in range(eff_level):
            steps.append(str(self.rng.choice(pool)))

        query: Dict[str, Any] = {
            "query_id": qid,
            "source_type": source,
            "complexity_level": int(eff_level),
            "logical_plan": {"steps": steps},
            # T004: ground_truth_plan must be a null placeholder.
            "ground_truth_plan": None,
            "synthetic_flag": True,
        }
        return query

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

    def save_queries(self, filepath: Path | str, count: int = 500) -> None:
        """Write generated queries to *filepath* as JSON."""
        path = Path(filepath) if not isinstance(filepath, Path) else filepath
        queries = self.generate_full_dataset(total=count)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(queries, f, indent=2)
        log.info("Saved %d synthetic queries to %s", len(queries), path)

def main() -> None:
    """CLI entry point to generate the synthetic query set."""
    output_path = paths.data("processed", "generation_log.json")
    gen = SyntheticQueryGenerator()
    gen.save_queries(output_path, count=500)

if __name__ == "__main__":
    main()
