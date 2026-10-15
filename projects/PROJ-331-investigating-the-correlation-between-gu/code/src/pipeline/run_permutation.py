"""Entry point for the permutation robustness test (Task T006).

This script provides a convenient CLI wrapper around the core
``run_permutation`` function defined in ``code.src.pipeline.permutation``.
It mirrors the style of the other ``run_*`` helper scripts in the
pipeline and can be invoked via:

    python -m src.pipeline.run_permutation --iterations 1000 --seed 42

The arguments are passed directly to ``run_permutation``; all defaults
match the specification (1 000 iterations, seed 42, a 4‑hour wall‑time
guard). The script returns exit code 0 on success.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from code.src.pipeline.permutation import run_permutation

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the permutation robustness test (Task T006)"
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=1000,
        help="Number of permutation iterations (default: 1000)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--clr",
        type=Path,
        help="Path to the CLR‑transformed abundances Parquet file "
             "(default: data/processed/clr_abundances.parquet)",
    )
    parser.add_argument(
        "--clinical",
        type=Path,
        help="Path to the clinical metadata Parquet file "
             "(default: data/raw/ppmi_clinical.parquet or open_clinical.parquet)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Output CSV path (default: results/permutation_pvalues.csv)",
    )
    parser.add_argument(
        "--max_wall_seconds",
        type=int,
        default=4 * 60 * 60,
        help="Maximum wall‑clock time for the whole permutation block "
             "(default: 4 hours)",
    )
    return parser.parse_args(argv)

def main(argv: list[str] | None = None) -> int:
    """Execute the permutation test and exit with a status code."""
    args = _parse_args(argv)

    run_permutation(
        iterations=args.iterations,
        seed=args.seed,
        clr_path=args.clr,
        clinical_path=args.clinical,
        out_path=args.out,
        max_wall_seconds=args.max_wall_seconds,
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())