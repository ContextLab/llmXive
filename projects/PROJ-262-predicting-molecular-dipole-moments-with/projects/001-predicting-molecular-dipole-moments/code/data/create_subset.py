"""
create_subset.py
----------------
Creates a reproducible random 10 000‑molecule subset of the QM9 dataset.

The script performs the following steps:
  1. Ensures the raw QM9 Parquet file exists (calls ``download_qm9`` if needed).
  2. Loads the raw data into a pandas DataFrame.
  3. Samples 10 000 rows using a fixed random seed (``SEED``) for reproducibility.
  4. Writes the subset to ``data/processed/molecules_10k.parquet``.

The output file is required by downstream preprocessing scripts and is listed in the
project’s quick‑start run‑book.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

# Import the download helper from the sibling module.
# The function is idempotent and will create the raw Parquet if missing.
from code.data.download_qm9 import download_and_save, RAW_PARQUET_PATH

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
SUBSET_PARQUET_PATH = PROCESSED_DIR / "molecules_10k.parquet"

# Fixed seed for reproducibility across runs and seeds used elsewhere in the project.
SEED = 42
SUBSET_SIZE = 10_000

# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #
def ensure_processed_dir() -> None:
    """Create the processed data directory if it does not exist."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def create_subset(df: pd.DataFrame, size: int, seed: int) -> pd.DataFrame:
    """
    Return a random subset of ``df`` with ``size`` rows using ``seed``.
    """
    if size > len(df):
        raise ValueError(
            f"Requested subset size {size} exceeds dataset size {len(df)}."
        )
    return df.sample(n=size, random_state=seed).reset_index(drop=True)

def main() -> None:
    """
    Execute the subset creation pipeline.
    """
    parser = argparse.ArgumentParser(
        description="Create a reproducible 10k random subset of QM9."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=SEED,
        help="Random seed for reproducibility (default: %(default)s).",
    )
    parser.add_argument(
        "--size",
        type=int,
        default=SUBSET_SIZE,
        help="Number of molecules in the subset (default: %(default)s).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the subset file if it already exists.",
    )
    args = parser.parse_args()

    # ------------------------------------------------------------------- #
    # 1️⃣ Ensure raw data exists
    # ------------------------------------------------------------------- #
    if not RAW_PARQUET_PATH.is_file():
        print(
            f"Raw QM9 parquet not found at {RAW_PARQUET_PATH}. "
            "Downloading now..."
        )
        try:
            download_and_save()
        except Exception as exc:
            print(f"Failed to download raw QM9 data: {exc}", file=sys.stderr)
            sys.exit(1)

    # ------------------------------------------------------------------- #
    # 2️⃣ Load raw data
    # ------------------------------------------------------------------- #
    try:
        raw_df = pd.read_parquet(RAW_PARQUET_PATH)
    except Exception as exc:
        print(f"Unable to read raw QM9 parquet: {exc}", file=sys.stderr)
        sys.exit(1)

    # ------------------------------------------------------------------- #
    # 3️⃣ Create (or reuse) the subset
    # ------------------------------------------------------------------- #
    if SUBSET_PARQUET_PATH.is_file() and not args.force:
        print(f"Subset already exists at {SUBSET_PARQUET_PATH}. Use --force to overwrite.")
        return

    subset_df = create_subset(raw_df, size=args.size, seed=args.seed)

    # ------------------------------------------------------------------- #
    # 4️⃣ Write the subset
    # ------------------------------------------------------------------- #
    ensure_processed_dir()
    subset_df.to_parquet(SUBSET_PARQUET_PATH, index=False)
    print(f"10k‑molecule subset written to {SUBSET_PARQUET_PATH}")

if __name__ == "__main__":
    main()