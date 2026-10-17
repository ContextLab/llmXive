"""
run_pipeline.py
----------------

Minimal end‑to‑end pipeline driver.  The full scientific pipeline will be
expanded in later tasks, but for the purpose of the initial integration
test we only need a deterministic entry point that:

1. Seeds all randomness sources.
2. Executes the data‑curation step (so that the expected output directories
   are created).
3. Prints the literal string ``Pipeline completed`` and exits with status 0.

The CLI accepts a ``--config`` argument for compatibility with the
Quickstart documentation, even though the current implementation does not
make use of the configuration file.
"""

import argparse
import sys
from src.curators.curate_failed_figures import curate_failed_figures
from src.run_pipeline import seed_all  # type: ignore  # will be defined below

__all__ = ["seed_all", "main"]

def seed_all(seed: int = 42) -> None:
    """
    Seed all randomness sources for reproducibility.
    """
    import random

    random.seed(seed)

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the full study pipeline."
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to a YAML configuration file (currently unused).",
    )
    return parser

def main() -> int:
    parser = _build_arg_parser()
    _ = parser.parse_args()  # config argument is ignored for now

    # Step 1: deterministic seeding
    seed_all()

    # Step 2: run the curation step (creates data/figures etc.)
    # Using the default values matches the Quickstart expectations.
    curate_failed_figures()

    # Future steps (simulation, validation, analysis) will be added here.

    print("Pipeline completed")
    return 0

if __name__ == "__main__":
    sys.exit(main())
