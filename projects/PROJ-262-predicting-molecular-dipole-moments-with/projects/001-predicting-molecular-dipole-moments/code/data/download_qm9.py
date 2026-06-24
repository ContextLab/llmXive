"""
download_qm9.py
----------------
Downloads the QM9 dataset using the 🤗 Datasets library and stores it as a Parquet file
in the project's raw data directory.

The script is idempotent: if the target file already exists it will be left untouched.
It is also safe to call from downstream scripts (e.g., ``create_subset.py``) which
may need the raw data but do not want to depend on a separate download step.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from datasets import load_dataset
import pandas as pd

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
RAW_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
RAW_PARQUET_PATH = RAW_DATA_DIR / "qm9.parquet"

# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #
def ensure_raw_dir() -> None:
    """Create the raw data directory if it does not exist."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

def download_and_save() -> Path:
    """
    Download the QM9 dataset from the HuggingFace hub and write it to a Parquet file.

    Returns
    -------
    Path
        Path to the written Parquet file.
    """
    # The QM9 dataset on the hub is available under the identifier "qm9".
    # It contains a single split named "train".  We load the entire split,
    # convert it to a pandas DataFrame and store it as Parquet (which is
    # efficient and supported by downstream code).
    dataset = load_dataset("qm9", split="train")
    df: pd.DataFrame = dataset.to_pandas()

    ensure_raw_dir()
    df.to_parquet(RAW_PARQUET_PATH, index=False)
    return RAW_PARQUET_PATH

# --------------------------------------------------------------------------- #
# CLI entry point
# --------------------------------------------------------------------------- #
def main() -> None:
    """
    Command‑line interface.

    The script can be invoked directly:
        python -m code.data.download_qm9
    """
    parser = argparse.ArgumentParser(
        description="Download the QM9 dataset and store it as Parquet."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re‑download even if the Parquet file already exists.",
    )
    args = parser.parse_args()

    if RAW_PARQUET_PATH.is_file() and not args.force:
        print(f"Raw QM9 Parquet already exists at {RAW_PARQUET_PATH}")
    else:
        print("Downloading QM9 dataset...")
        path = download_and_save()
        print(f"QM9 dataset written to {path}")

if __name__ == "__main__":
    main()