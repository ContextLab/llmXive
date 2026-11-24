"""Command-line entry point for synthetic query generation.

This script instantiates the SyntheticQueryGenerator and writes the 
resulting query instances to data/processed/generation_log.json.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from llmxive_toolkit import get_logger, paths
from generators.synthetic_query import SyntheticQueryGenerator

log = get_logger(__name__)

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate synthetic queries for the benchmark pipeline."
    )
    parser.add_argument(
        "--levels",
        nargs="+",
        type=int,
        default=[1, 2, 3, 4],
        help="List of integer complexity levels to generate.",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=500,
        help="Total number of queries to generate.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic generation.",
    )
    return parser.parse_args()

def main() -> None:
    args = _parse_args()

    # Initialize the generator
    generator = SyntheticQueryGenerator(seed=args.seed, levels=args.levels)

    output_path = paths.data("processed", "generation_log.json")
    log.info(
        "Generating %d synthetic queries (levels=%s) -> %s",
        args.count,
        args.levels,
        output_path,
    )
    
    # This will generate queries, validate them against the schema, and save them.
    generator.save_queries(output_path, count=args.count)
    
    # Verification of the US-2 requirement: at least 100 high-complexity graph queries.
    # We can check this by loading the file back.
    with output_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    
    high_comp_graph = [
        q for q in data 
        if q["source_type"] == "graph" and q["complexity_level"] >= 3
    ]
    log.info("Verification: Found %d high-complexity graph queries", len(high_comp_graph))
    
    if len(high_comp_graph) < 100:
        log.warning(
            "High-complexity graph query count (%d) is below target (100).",
            len(high_comp_graph),
        )
    
    log.info("Synthetic query generation completed successfully.")

if __name__ == "__main__":
    main()