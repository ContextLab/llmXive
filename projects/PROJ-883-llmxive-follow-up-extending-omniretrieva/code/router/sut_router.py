"""Unified router for generating system‑generated execution plans.

This script reads a JSON file containing query definitions (as produced by
``SyntheticQueryGenerator``), enriches each entry with a ``sut_plan`` field
using a limited‑lookahead (depth‑1) heuristic, and writes the updated JSON
back to disk.

The heuristic is deliberately lightweight: for a given ``source_type``
we assign a static base operation and cost.  The ``sut_plan`` consists of
a list of steps whose length matches the query's ``complexity_level``.
Each step repeats the base operation, representing a depth‑1 look‑ahead
estimate of the work required.

The script is invoked via the quick‑start guide and can be run directly:

    python code/router/sut_router.py --input data/processed/generation_log.json \\
                                    --output data/processed/generation_log.json
"""

import argparse
import json
from pathlib import Path
from typing import List, Dict, Any

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Heuristic definitions
# ----------------------------------------------------------------------
# Base operation and static cost for each source type.  These are simple
# stand‑ins for a real cost model; they satisfy FR‑004's requirement for a
# system‑generated plan without introducing external data sources.
SOURCE_OPERATIONS = {
    "text": {"op": "retrieve_text", "base_cost": 1},
    "relational": {"op": "execute_sql", "base_cost": 2},
    "graph": {"op": "run_sparql", "base_cost": 3},
}

def _generate_sut_plan(query: Dict[str, Any]) -> Dict[str, Any]:
    """Create a system‑generated plan for a single query.

    The plan contains:
    - ``estimated_cost``: ``base_cost * complexity_level``.
    - ``steps``: a list of operation names, length equal to
      ``complexity_level`` (limited look‑ahead of depth‑1).

    Parameters
    ----------
    query: dict
        One entry from the generation log.

    Returns
    -------
    dict
        The ``sut_plan`` to be inserted into the query record.
    """
    source = query.get("source_type")
    complexity = int(query.get("complexity_level", 1))

    if source not in SOURCE_OPERATIONS:
        log.warning(
            "Unknown source_type '%s' – defaulting to generic operation.",
            source,
        )
        op_info = {"op": "generic_operation", "base_cost": 1}
    else:
        op_info = SOURCE_OPERATIONS[source]

    estimated_cost = op_info["base_cost"] * complexity
    steps = [op_info["op"] for _ in range(complexity)]

    return {
        "estimated_cost": estimated_cost,
        "steps": steps,
    }

# ----------------------------------------------------------------------
# CLI handling
# ----------------------------------------------------------------------
def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Enrich generation_log.json with system‑generated plans."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to the input generation_log.json file.",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path where the enriched JSON will be written.",
    )
    return parser.parse_args()

def main() -> None:
    args = _parse_args()
    # Use plain pathlib.Path to allow both project‑relative and external
    # temporary paths (e.g., during unit tests).  ``paths.path`` enforces
    # the path to be inside the project root, which caused test failures.
    input_path = Path(args.input)
    output_path = Path(args.output)

    log.info("Reading generation log from %s", input_path)
    with open(input_path, "r", encoding="utf-8") as f:
        try:
            queries: List[Dict[str, Any]] = json.load(f)
        except json.JSONDecodeError as exc:
            log.error("Failed to parse JSON: %s", exc)
            raise

    if not isinstance(queries, list):
        raise ValueError(
            f"Expected a list of query objects in {input_path}, got {type(queries)}"
        )

    log.info("Generating system‑generated plans for %d queries", len(queries))
    for query in queries:
        # Preserve existing fields; add/overwrite ``sut_plan``.
        query["sut_plan"] = _generate_sut_plan(query)

    # Ensure the parent directory exists.
    output_path.parent.mkdir(parents=True, exist_ok=True)

    log.info("Writing enriched generation log to %s", output_path)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(queries, f, indent=2)

    log.info("Router finished successfully.")

if __name__ == "__main__":
    main()