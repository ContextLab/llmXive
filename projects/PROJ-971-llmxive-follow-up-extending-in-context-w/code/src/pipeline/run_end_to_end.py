"""
Minimal end‑to‑end driver for the Auto‑ICWM pipeline.

This script orchestrates the three core steps required for the
“minimal” run‑book used by the quickstart:

1. Generate a reproducible set of interaction clips (CartPole) in
   ``data/raw``.
2. Extract the three statistical descriptors (variance,
   lag‑1 autocorrelation, Welch spectral density) for *all* clips
   and write the full table to ``data/processed/descriptors.csv``.
3. Create a legacy shortcut CSV containing the first ``N`` rows
   (default 50) at ``data/descriptors_subset.csv`` and print the
   subset table to ``stdout`` for visual inspection.

The script is deliberately idempotent – it overwrites any existing
files so that a fresh run always yields the same deterministic
output (fixed random seeds are used throughout the pipeline).

Usage
-----
``python -m src.pipeline.run_end_to_end --subset 50``
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

from llmxive_toolkit import paths, get_logger
from src.pipeline.generate_clips import generate_clips
from src.pipeline.extract_descriptors import extract_all_descriptors

log = get_logger(__name__)

def _parse_args(argv: list | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the minimal end‑to‑end Auto‑ICWM pipeline."
    )
    parser.add_argument(
        "--subset",
        type=int,
        default=50,
        help="Number of rows to include in the legacy subset CSV "
             "(and to print). Must be ≤ the total number of generated clips.",
    )
    return parser.parse_args(argv)

def _generate_clips(num_clips: int, raw_dir: Path) -> None:
    """Generate ``num_clips`` reproducible CartPole interaction clips."""
    log.info("Generating %d interaction clips in %s", num_clips, raw_dir)
    generate_clips(num_clips=num_clips, out_dir=raw_dir)

def _extract_descriptors(raw_dir: Path, full_csv: Path) -> None:
    """Extract descriptors for all ``*.npz`` files in ``raw_dir``."""
    log.info("Extracting descriptors from %s → %s", raw_dir, full_csv)
    extract_all_descriptors(input_dir=raw_dir, output_path=full_csv)

def _write_subset(full_csv: Path, subset_csv: Path, n: int) -> pd.DataFrame:
    """Write the first ``n`` rows of ``full_csv`` to ``subset_csv``."""
    df_full = pd.read_csv(full_csv)
    df_subset = df_full.head(n).copy()
    df_subset.to_csv(subset_csv, index=False)
    log.info("Wrote subset CSV with %d rows to %s", n, subset_csv)
    return df_subset

def main(argv: list | None = None) -> None:
    args = _parse_args(argv)

    # Resolve paths using the toolkit helpers – they create parent dirs.
    raw_dir = paths.data("raw")
    full_csv = paths.data("processed", "descriptors.csv")
    subset_csv = paths.data("descriptors_subset.csv")

    # Step 1 – generate clips.
    _generate_clips(num_clips=args.subset, raw_dir=raw_dir)

    # Step 2 – extract full descriptor table.
    _extract_descriptors(raw_dir=raw_dir, full_csv=full_csv)

    # Step 3 – create and print the subset.
    df_subset = _write_subset(full_csv=full_csv, subset_csv=subset_csv, n=args.subset)

    # Print a clean table (no pandas index) to stdout.
    print(df_subset.to_string(index=False))

if __name__ == "__main__":
    # When invoked as a script ``python -m src.pipeline.run_end_to_end``
    # we forward the command‑line arguments verbatim.
    main(sys.argv[1:])