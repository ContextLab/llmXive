"""
src/models/split.py
-------------------

Deterministic 80/20 train‑test split that respects composition groups.
This implementation writes the split CSVs, a log file, and SHA‑256
checksum files for both outputs, satisfying the unit tests
(tests/test_split.py).

The public API consists of ``split_dataset`` and ``main``.  ``split_dataset``
returns the train and test DataFrames for programmatic use, while ``main``
provides a CLI entry point used by the test suite.
"""

import argparse
import sys
from pathlib import Path
from typing import Tuple

import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

from llmxive_toolkit import get_logger, paths
from src.utils.checksum import write_checksum

log = get_logger(__name__)

def split_dataset(
    features_path: Path,
    train_path: Path,
    test_path: Path,
    test_size: float = 0.2,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Perform a deterministic group‑aware train/test split.

    Parameters
    ----------
    features_path : Path
        Path to the input feature matrix CSV (must contain a ``composition``
        column).
    train_path : Path
        Destination for the training split CSV.
    test_path : Path
        Destination for the test split CSV.
    test_size : float, optional
        Fraction of the dataset to allocate to the test split (default 0.2).
    random_state : int, optional
        Random seed for reproducibility (default 42).

    Returns
    -------
    Tuple[pd.DataFrame, pd.DataFrame]
        The training and test DataFrames.
    """
    # Load the full feature matrix.
    df = pd.read_csv(features_path)

    if "composition" not in df.columns:
        raise ValueError(
            "Input feature matrix must contain a 'composition' column for grouping."
        )

    groups = df["composition"]
    splitter = GroupShuffleSplit(
        n_splits=1, test_size=test_size, random_state=random_state
    )
    train_idx, test_idx = next(splitter.split(df, groups=groups))

    train_df = df.iloc[train_idx].reset_index(drop=True)
    test_df = df.iloc[test_idx].reset_index(drop=True)

    # Sanity check: ensure no overlapping groups.
    overlap = set(train_df["composition"]).intersection(set(test_df["composition"]))
    if overlap:
        raise RuntimeError(
            f"Group overlap detected between train and test sets: {overlap}"
        )

    # Write CSV files.
    for out_path, out_df in [(train_path, train_df), (test_path, test_df)]:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_df.to_csv(out_path, index=False)

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------
    split_log_path = paths.data("processed", "split.log")
    split_log_path.parent.mkdir(parents=True, exist_ok=True)
    with split_log_path.open("w", encoding="utf-8") as log_file:
        log_file.write(
            f"Split completed: {len(train_df)} training rows, {len(test_df)} test rows.\\n"
        )
        log_file.write(
            f"Training groups: {len(set(train_df['composition']))}\\n"
        )
        log_file.write(f"Test groups: {len(set(test_df['composition']))}\\n"
        )
    log.info(f"Split log written to {split_log_path}")

    # ------------------------------------------------------------------
    # Checksums
    # ------------------------------------------------------------------
    checksums_dir = paths.data("checksums")
    checksums_dir.mkdir(parents=True, exist_ok=True)

    write_checksum(train_path, checksums_dir)
    write_checksum(test_path, checksums_dir)

    log.info(f"Checksums written to {checksums_dir}")

    return train_df, test_df

def main() -> None:
    """
    CLI entry point.

    Expected positional arguments:
    1. Path to the input feature matrix CSV.
    2. Path to write the training split CSV.
    3. Path to write the test split CSV.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Deterministic 80/20 train‑test split respecting composition groups."
        )
    )
    parser.add_argument(
        "features_csv", type=str, help="Path to the input feature matrix CSV."
    )
    parser.add_argument(
        "train_csv", type=str, help="Path to write the training split CSV."
    )
    parser.add_argument(
        "test_csv", type=str, help="Path to write the test split CSV."
    )
    args = parser.parse_args()

    split_dataset(
        Path(args.features_csv),
        Path(args.train_csv),
        Path(args.test_csv),
    )

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log.error(str(exc))
        sys.exit(1)