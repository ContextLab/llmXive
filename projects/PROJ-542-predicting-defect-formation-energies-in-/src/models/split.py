"""
src/models/split.py
-------------------

Implements a deterministic, composition‑aware train/test split using
scikit‑learn's ``GroupShuffleSplit``.  The split respects the requirement
that no composition appears in both the training and test sets and that the
proportion is 80 % / 20 % (default).  SHA‑256 checksums for the generated CSV
files are written to ``data/checksums`` and a short log is created in
``data/processed``.
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
    if not features_path.is_file():
        raise FileNotFoundError(f"Features file not found at {features_path}")

    # Load the full feature matrix.
    df = pd.read_csv(features_path)

    if "composition" not in df.columns:
        raise ValueError("Input features must contain a 'composition' column.")

    # Use the composition column as the grouping key.
    groups = df["composition"].values

    splitter = GroupShuffleSplit(
        test_size=test_size, n_splits=1, random_state=random_state
    )
    train_idx, test_idx = next(splitter.split(df, groups=groups))

    train_df = df.iloc[train_idx].reset_index(drop=True)
    test_df = df.iloc[test_idx].reset_index(drop=True)

    # Write the split CSVs.
    train_path.parent.mkdir(parents=True, exist_ok=True)
    test_path.parent.mkdir(parents=True, exist_ok=True)
    train_df.to_csv(train_path, index=False)
    test_df.to_csv(test_path, index=False)

    # Log summary information.
    log_path = paths.data("processed", "split.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as log_f:
        log_f.write(
            f"Split completed: {len(train_df)} training rows, {len(test_df)} test rows.\\n"
        )
        log_f.write(
            f"Training groups: {train_df['composition'].nunique()}\\n"
        )
        log_f.write(f"Test groups: {test_df['composition'].nunique()}\\n")
    log.info(
        "Train/test split written: %s (train), %s (test)", train_path, test_path
    )

    # Write checksums for the two output files.
    checksum_dir = paths.data("checksums")
    write_checksum(train_path, checksum_dir)
    write_checksum(test_path, checksum_dir)

    return train_df, test_df

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
        help="Path where the training CSV will be written.",
    )
    parser.add_argument(
        "test_path",
        type=Path,
        help="Path where the test CSV will be written.",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Proportion of the dataset to allocate to the test set (default 0.2).",
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
    CLI entry point. Parses positional arguments and delegates to
    ``split_dataset``.  The function exits with status 0 on success; any
    exception propagates to the caller (the test suite expects a non‑zero
    exit code on failure).
    """
    args = _parse_cli_args()
    split_dataset(
        features_path=args.features_path,
        train_path=args.train_path,
        test_path=args.test_path,
        test_size=args.test_size,
        random_state=args.random_state,
    )

if __name__ == "__main__":
    sys.exit(main())
