"""
verify_diversity.py
-------------------

This script verifies that the set of cleaned datasets downloaded by the
pipeline contains sufficient diversity:

* At least two *numerical‑only* datasets (all columns are numeric)
* At least two *categorical‑only* datasets (all columns are non‑numeric)

Datasets are expected to reside in ``data/raw/cleaned/`` as CSV files.
The script inspects each CSV, classifies it, and raises an error if the
diversity criteria are not met.  It is intended to be called as the final
step of the download‑clean pipeline (see ``code/download.py``).

The script exits with a non‑zero status code when the requirements are
violated, causing the overall pipeline to fail loudly.
"""

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

def classify_dataset(df: pd.DataFrame) -> str:
    """
    Classify a DataFrame as ``numerical``, ``categorical`` or ``mixed``.

    * ``numerical``   – every column has a numeric dtype.
    * ``categorical`` – every column is non‑numeric (object, category, bool).
    * ``mixed``       – any mixture of numeric and non‑numeric columns.
    """
    if df.empty:
        # An empty dataset cannot be classified; treat it as mixed.
        return "mixed"

    numeric_cols = df.select_dtypes(include=["number"]).columns
    non_numeric_cols = df.columns.difference(numeric_cols)

    if len(numeric_cols) == len(df.columns):
        return "numerical"
    if len(non_numeric_cols) == len(df.columns):
        return "categorical"
    return "mixed"

def verify_dataset_diversity(cleaned_dir: Path) -> None:
    """
    Verify that the cleaned dataset collection satisfies the diversity
    constraints required by task **T019e**.

    Parameters
    ----------
    cleaned_dir: Path
        Directory that contains the cleaned CSV files.
    """
    if not cleaned_dir.is_dir():
        raise FileNotFoundError(f"Cleaned data directory not found: {cleaned_dir}")

    csv_files = list(cleaned_dir.glob("*.csv"))
    if not csv_files:
        raise ValueError(f"No CSV files found in {cleaned_dir}")

    counts = {"numerical": 0, "categorical": 0, "mixed": 0}
    for csv_path in csv_files:
        try:
            df = pd.read_csv(csv_path)
        except Exception as exc:
            logger.error("Failed to read %s: %s", csv_path, exc)
            continue

        classification = classify_dataset(df)
        counts[classification] += 1
        logger.info("Dataset %s classified as %s", csv_path.name, classification)

    logger.info("Dataset diversity counts: %s", counts)

    if counts["numerical"] < 2:
        raise AssertionError(
            f"Insufficient numerical‑only datasets: found {counts['numerical']}, "
            "required ≥ 2."
        )
    if counts["categorical"] < 2:
        raise AssertionError(
            f"Insufficient categorical‑only datasets: found {counts['categorical']}, "
            "required ≥ 2."
        )
    logger.info("Dataset diversity verification passed.")

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify diversity of cleaned datasets for T019e."
    )
    parser.add_argument(
        "--cleaned-dir",
        type=Path,
        default=Path("data/raw/cleaned"),
        help="Directory containing cleaned CSV files (default: data/raw/cleaned).",
    )
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    try:
        verify_dataset_diversity(args.cleaned_dir)
    except Exception as exc:
        logger.error("Dataset diversity verification failed: %s", exc)
        sys.exit(1)

if __name__ == "__main__":
    main()
