"""
Minimal end‑to‑end driver for the Auto‑ICWM pipeline.

This script orchestrates the two previously implemented steps:
1. Generate a reproducible set of interaction clips.
2. Extract statistical descriptors from each clip.

After the two steps it loads the resulting CSV and prints a concise
summary table.  The CI verification expects exactly ``subset`` rows
(default 50) and the three descriptor columns to be present.
"""
import argparse
from pathlib import Path

import pandas as pd

# Toolkit helpers for deterministic paths
from llmxive_toolkit import paths, get_logger

# Import the two pipeline stages we already implemented
from src.pipeline.generate_clips import generate_clips
from src.pipeline.extract_descriptors import extract_all_descriptors

log = get_logger(__name__)

def _run_pipeline(num_clips: int) -> Path:
    """
    Run the full minimal pipeline.

    Parameters
    ----------
    num_clips : int
        Number of clips to generate and process.

    Returns
    ----------
    Path
        Path to the generated descriptor CSV file.
    """
    # ------------------------------------------------------------------
    # 1️⃣  Generate reproducible interaction clips
    # ------------------------------------------------------------------
    raw_dir: Path = paths.data("raw")
    log.info("Generating %d clips in %s", num_clips, raw_dir)
    generate_clips(num_clips=num_clips, out_dir=raw_dir)

    # ------------------------------------------------------------------
    # 2️⃣  Extract statistical descriptors
    # ------------------------------------------------------------------
    descriptors_path: Path = paths.data("descriptors_subset.csv")
    log.info("Extracting descriptors from %s → %s", raw_dir, descriptors_path)
    extract_all_descriptors(input_dir=raw_dir, output_path=descriptors_path)

    return descriptors_path

def _print_summary(csv_path: Path) -> None:
    """
    Load the descriptor CSV and print a human‑readable summary table.

    The table includes the ``clip_id`` and the three descriptor columns.
    The CI check expects the full set of rows (e.g., 50) to be printed.
    """
    df = pd.read_csv(csv_path)
    # Ensure the expected columns exist; raise a clear error otherwise.
    expected_cols = {"clip_id", "variance", "autocorr_lag1", "spectral_density"}
    missing = expected_cols - set(df.columns)
    if missing:
        raise RuntimeError(f"Descriptor CSV missing columns: {missing}")

    # Sort by clip_id for deterministic ordering
    df_sorted = df.sort_values(by="clip_id").reset_index(drop=True)

    # Print the entire table (no truncation)
    print("\nDescriptor summary (all rows):")
    print(df_sorted.to_string(index=False))
    print(f"\nTotal rows: {len(df_sorted)}")

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the minimal Auto‑ICWM end‑to‑end pipeline."
    )
    parser.add_argument(
        "--subset",
        type=int,
        default=50,
        help="Number of interaction clips to generate and process (default: 50).",
    )
    args = parser.parse_args()

    descriptors_path = _run_pipeline(num_clips=args.subset)
    _print_summary(descriptors_path)

if __name__ == "__main__":
    main()
