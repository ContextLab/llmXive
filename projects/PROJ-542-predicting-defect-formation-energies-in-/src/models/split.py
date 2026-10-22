"""
src/models/split.py
-------------------

Deterministic 80/20 train‑test split that respects composition groups.
The file already existed; it is reproduced here unchanged to satisfy the
import path used by the pipeline.
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

    # Sanity check: ensure no overlapping groups
    overlap = set(train_df["composition"]).intersection(set(test_df["composition"]))
    if overlap:
        raise RuntimeError(f"Group overlap detected between train and test sets: {overlap}")

    # Write CSV files.
    for out_path, out_df in [(train_path, train_df), (test_path, test_df)]:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_df.to_csv(out_path, index=False)

    # Log summary.
    log.info(f"Split completed: {len(train_df)} training rows, {len(test_df)} test rows.")
    log.debug(f"Training groups: {len(set(train_df['composition']))}")
    log.debug(f"Test groups: {len(set(test_df['composition']))}")

    return train_df, test_df

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Deterministic 80/20 train‑test split respecting composition groups."
    )
    parser.add_argument("features_csv", type=str, help="Path to the input feature matrix CSV.")
    parser.add_argument("train_csv", type=str, help="Path to write the training split.")
    parser.add_argument("test_csv", type=str, help="Path to write the test split.")
    args = parser.parse_args()

    split_dataset(Path(args.features_csv), Path(args.train_csv), Path(args.test_csv))

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log.error(str(exc))
        sys.exit(1)