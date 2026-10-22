"""
src/models/split.py
-------------------

Implements a deterministic, composition‑aware train/test split using
``GroupShuffleSplit``.  The module provides a library function
``split_dataset`` and a CLI entry point ``main`` that is exercised by the
test suite.

The split respects the following requirements:
* 80 % / 20 % split (configurable via ``--test-size``).
* Groups are defined by the ``composition`` column – no composition appears
  in both the training and test sets.
* Random state is fixed at 42 by default for reproducibility.
* After splitting, the CSV files are written, a log file is emitted, and
  SHA‑256 checksum files are generated for both CSVs.

The checksum utility is provided by ``src.utils.checksum.write_checksum``.
"""

import argparse
import sys
from pathlib import Path
from typing import Tuple

import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

from src.utils.checksum import write_checksum

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
        raise ValueError("Input features must contain a 'composition' column.")

    # Use the composition string as the grouping key.
    groups = df["composition"].astype(str)

    splitter = GroupShuffleSplit(
        n_splits=1, test_size=test_size, random_state=random_state
    )
    train_idx, test_idx = next(splitter.split(df, groups=groups))

    train_df = df.iloc[train_idx].reset_index(drop=True)
    test_df = df.iloc[test_idx].reset_index(drop=True)

    # Write out the CSV files.
    train_path.parent.mkdir(parents=True, exist_ok=True)
    test_path.parent.mkdir(parents=True, exist_ok=True)
    train_df.to_csv(train_path, index=False)
    test_df.to_csv(test_path, index=False)

    return train_df, test_df

def _write_log(train_df: pd.DataFrame, test_df: pd.DataFrame) -> None:
    """
    Write a simple log file summarising the split.
    """
    log_path = Path("data/processed/split.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Count unique composition groups in each split.
    train_groups = train_df["composition"].nunique()
    test_groups = test_df["composition"].nunique()

    log_contents = (
        f"Split completed: {len(train_df)} training rows, {len(test_df)} test rows.\n"
        f"Training groups: {train_groups}\n"
        f"Test groups: {test_groups}\n"
    )
    log_path.write_text(log_contents)

def _parse_cli_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Deterministic composition‑aware train/test split."
    )
    parser.add_argument(
        "features_path",
        type=Path,
        help="Path to the input feature matrix CSV.",
    )
    parser.add_argument(
        "train_path",
        type=Path,
        help="Destination path for the training CSV.",
    )
    parser.add_argument(
        "test_path",
        type=Path,
        help="Destination path for the test CSV.",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Proportion of the dataset to use as test set (default 0.2).",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Random seed for reproducibility (default 42).",
    )
    return parser.parse_args()

def main() -> None:
    """
    CLI entry point – parses arguments, performs the split, writes the
    log file and checksum artefacts.
    """
    args = _parse_cli_args()

    train_df, test_df = split_dataset(
        features_path=args.features_path,
        train_path=args.train_path,
        test_path=args.test_path,
        test_size=args.test_size,
        random_state=args.random_state,
    )

    # Write the split log.
    _write_log(train_df, test_df)

    # Generate SHA‑256 checksum files for both CSVs.
    checksums_dir = Path("data/checksums")
    write_checksum(args.train_path, checksums_dir)
    write_checksum(args.test_path, checksums_dir)

if __name__ == "__main__":
    # When executed via ``python -m src.models.split``.
    main()