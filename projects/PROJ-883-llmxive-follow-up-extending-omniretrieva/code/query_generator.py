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

def _parse_int(value: str) -> int:
    """
    Parse an integer from a string, falling back to a default when the
    input is a placeholder such as ``[sufficient sample size]``.
    """
    try:
        return int(value)
    except ValueError:
        # Recognise common placeholder patterns and replace them with a
        # sensible default.  The default mirrors the value used in the
        # main pipeline (10 queries per depth level).
        log.warning(
            "Received placeholder count value '%s'; using default of 10.",
            value,
        )
        return 10

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
    # ``--count`` may be supplied as a single integer or as a placeholder
    # token sequence like ``[sufficient sample size]``.  Using ``nargs='+'``
    # captures all following tokens up to the next flag.
    parser.add_argument(
        "--count",
        nargs="+",
        default=["10"],
        help=(
            "Number of queries to generate per depth level. "
            "Accepts an integer or a placeholder such as "
            "'[sufficient sample size]'."
        ),
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
    # ``args.count`` is a list of tokens; join them back into a single
    # string before converting to int (or falling back to the default).
    count_str = " ".join(args.count)
    count_per_level = _parse_int(count_str)

    generator = SyntheticQueryGenerator(
        levels=args.levels,
        count_per_level=count_per_level,
        seed=args.seed,
    )
    generator.write_to_file(args.output)
    log.info(
        "Synthetic query generation completed. Output written to %s",
        args.output,
    )


if __name__ == "__main__":
    main()
