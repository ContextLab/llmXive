"""Synthetic query generator.

Generates queries with integer plan depths and attaches a deterministic
ground‑truth plan using the ReferenceEngine. The generated queries are
written to a JSON file that conforms to ``query_instance.schema.yaml``.
"""

import json
import random
from typing import List, Dict, Any
from pathlib import Path

from llmxive_toolkit import get_logger, paths
from .reference_engine import ReferenceEngine

log = get_logger(__name__)

# The maximum depth we support for synthetic generation.  If a caller
# requests a larger depth we cap it and emit a warning.
MAX_DEPTH = 4


class SyntheticQueryGenerator:
    """Generate synthetic queries with integer depth."""

    def __init__(self, levels: List[int], count_per_level: int = 10, seed: int = 42):
        """
        Parameters
        ----------
        levels: List[int]
            Desired plan depths (e.g., [1, 2, 3, 4]).
        count_per_level: int
            How many queries to emit for each depth level.
        seed: int
            Random seed for reproducibility.
        """
        self.levels = levels
        self.count_per_level = count_per_level
        self.rng = random.Random(seed)
        self.ref_engine = ReferenceEngine()

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

    def generate(self) -> List[Dict[str, Any]]:
        """Create a list of query definitions."""
        queries: List[Dict[str, Any]] = []
        for level in self.levels:
            eff_level = self._effective_level(level)
            for _ in range(self.count_per_level):
                qid = f"q_{level}_{self.rng.randint(0, 1_000_000)}"
                query: Dict[str, Any] = {
                    "query_id": qid,
                    "source_type": self.rng.choice(["text", "relational", "graph"]),
                    "complexity_level": int(eff_level),  # persisted as integer
                    "logical_plan": {"steps": []},  # placeholder – schema allows empty steps
                }
                # Attach deterministic ground‑truth plan using the reference engine.
                gt_plan = self.ref_engine.generate_plan(query)
                query["ground_truth_plan"] = gt_plan
                queries.append(query)
        return queries

    def write_to_file(self, filepath: Path | str) -> None:
        """Write the generated queries to ``filepath`` as JSON.

        The directory hierarchy is created if it does not already exist.
        """
        # Accept both ``Path`` objects and plain strings.
        path = Path(filepath) if not isinstance(filepath, Path) else filepath
        # Ensure the file lives inside the project root.
        path = paths.path(str(path))
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.generate(), f, indent=2)
