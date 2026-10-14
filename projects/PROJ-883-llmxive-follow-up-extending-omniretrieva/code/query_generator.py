"""CLI wrapper for the SyntheticQueryGenerator.

This script is invoked by the quick‑start guide and is responsible for
materialising a ``generation_log.json`` file under ``data/processed/``.
The file contains one entry per synthetic query, each enriched with a
deterministic ground‑truth plan produced by the reference engine.
"""

import argparse
from pathlib import Path

from llmxive_toolkit import paths, get_logger
from generators.synthetic_query import SyntheticQueryGenerator

log = get_logger(__name__)

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate synthetic queries with explicit integer depths."
    )
    parser.add_argument(
        "--levels",
        nargs="+",
        type=int,
        required=True,
        help="List of integer plan depths to generate (e.g., 1 2 3 4).",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Number of queries to generate per depth level.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(paths.data("processed", "generation_log.json")),
        help="Path where the generation log JSON will be written.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    generator = SyntheticQueryGenerator(
        levels=args.levels,
        count_per_level=args.count,
        seed=args.seed,
    )
    generator.write_to_file(args.output)
    log.info("Synthetic query generation completed. Output written to %s", args.output)


if __name__ == "__main__":
    main()