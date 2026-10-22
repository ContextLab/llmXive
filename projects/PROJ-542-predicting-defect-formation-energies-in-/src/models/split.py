"""
src/models/split.py
-------------------

The implementation is unchanged from the original version; it already
provides a correct ``split_dataset`` function and a robust CLI entry
point that can be invoked via:

    python -m src.models.split <features_csv> <train_csv> <test_csv>

No modifications are required for the current task.
"""
import argparse
import sys
from pathlib import Path
from typing import Tuple

import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

def split_dataset(
    features_path: Path,
    train_path: Path,
    test_path: Path,
    test_size: float = 0.2,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Perform a deterministic train‑test split on the feature matrix.

    Parameters
    ----------
    features_path : Path
        Path to the input ``features.csv`` produced by ``src.featurize``.
    train_path : Path
        Destination path for the training split CSV.
    test_path : Path
        Destination path for the test split CSV.
    test_size : float, optional
        Fraction of the dataset to allocate to the test split (default 0.2).
    random_state : int, optional
        Seed for reproducibility (default 42).

    Returns
    -------
    Tuple[pd.DataFrame, pd.DataFrame]
        The training and test DataFrames (in that order).

    Raises
    ------
    ValueError
        If the required ``composition`` column is missing.
    RuntimeError
        If any composition appears in both splits (should never happen).
    """
    # Load the full feature matrix
    df = pd.read_csv(features_path)

    if "composition" not in df.columns:
        raise ValueError(
            "Input feature matrix must contain a 'composition' column for grouping."
        )

    # Define groups by composition string
    groups = df["composition"]

    # Use GroupShuffleSplit to keep groups intact
    splitter = GroupShuffleSplit(
        n_splits=1, test_size=test_size, random_state=random_state
    )
    train_idx, test_idx = next(splitter.split(df, groups=groups))

    train_df = df.iloc[train_idx].reset_index(drop=True)
    test_df = df.iloc[test_idx].reset_index(drop=True)

    # Sanity check: ensure no overlapping groups
    train_groups = set(train_df["composition"])
    test_groups = set(test_df["composition"])
    overlap = train_groups.intersection(test_groups)
    if overlap:
        raise RuntimeError(
            f"Group overlap detected between train and test sets: {overlap}"
        )

    # Write CSV files, creating parent directories if needed
    for out_path, out_df in [(train_path, train_df), (test_path, test_df)]:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_df.to_csv(out_path, index=False)

    # Log summary information
    log.info(
        f"Split completed: {len(train_df)} training rows, {len(test_df)} test rows."
    )
    log.debug(f"Training groups: {len(train_groups)} unique compositions.")
    log.debug(f"Test groups: {len(test_groups)} unique compositions.")
    return train_df, test_df

def main() -> None:
    """
    CLI entry point.

    Expected positional arguments:
        1. Path to the input features CSV.
        2. Path where the training CSV should be written.
        3. Path where the test CSV should be written.
    """
    parser = argparse.ArgumentParser(
        description="Deterministic 80/20 train‑test split respecting composition groups."
    )
    parser.add_argument(
        "features_csv",
        type=str,
        help="Path to the input feature matrix CSV (e.g., data/processed/features.csv).",
    )
    parser.add_argument(
        "train_csv",
        type=str,
        help="Path to write the training split (e.g., data/processed/train.csv).",
    )
    parser.add_argument(
        "test_csv",
        type=str,
        help="Path to write the test split (e.g., data/processed/test.csv).",
    )
    args = parser.parse_args()

    features_path = Path(args.features_csv)
    train_path = Path(args.train_csv)
    test_path = Path(args.test_csv)

    # Perform the split
    split_dataset(features_path, train_path, test_path)

if __name__ == "__main__":
    # When executed as a script, exit with the appropriate status code.
    try:
        main()
    except Exception as exc:
        log.error(str(exc))
        sys.exit(1)