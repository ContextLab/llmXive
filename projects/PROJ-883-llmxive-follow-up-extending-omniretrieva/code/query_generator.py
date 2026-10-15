"""Command‑line entry point for synthetic query generation.

The module is invoked by ``code.main`` via a subprocess call:

``python -m code.query_generator --levels 1 2 3 4 --count 10 --seed 42``

It parses the arguments, instantiates :class:`SyntheticQueryGenerator`,
and writes the generated queries to ``data/processed/generation_log.json``.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from llmxive_toolkit import get_logger, paths

# Import the updated generator.
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
        default=10,
        help="Total number of queries to generate (distributed across levels).",
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

    # The generator defaults to the canonical levels; we honour any
    # user‑provided list for flexibility.
    generator = SyntheticQueryGenerator(seed=args.seed, levels=args.levels)

    output_path = paths.data("processed", "generation_log.json")
    log.info("Generating %d synthetic queries (levels=%s) → %s", args.count, args.levels, output_path)
    generator.save_queries(output_path, count=args.count)
    log.info("Synthetic query generation completed.")


if __name__ == "__main__":
    main()
