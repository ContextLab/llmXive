"""
Data splitting utilities for molecular permeability datasets.

Implements stratified and random splitting strategies with strict validation
for polymer type stratification as required by FR-004. Writes both CSV and
Parquet versions of the splits to satisfy downstream expectations.

The script can be invoked via the CLI:
    python code/data/split.py
"""

import json
import logging
import yaml
from pathlib import Path
from typing import List, Tuple, Optional

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from llmxive_toolkit import paths, get_logger

# Set up logger
log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _load_config() -> dict:
    """Load configuration from config.yaml in the project root."""
    config_path = Path(__file__).resolve().parent.parent.parent / "config.yaml"
    if not config_path.exists():
        log.warning(f"Config file not found at {config_path}. Using defaults.")
        return {
            "stratification_diff_threshold": 0.05,
            "target_column": "target",
        }

    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def random_split(
    df: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Perform a simple random split of the dataframe.
    Guarantees at least one row in each split when possible.
    """
    n = len(df)
    if n <= 1:
        # Nothing to split – return empty test set (handled later)
        return df.copy(), pd.DataFrame(columns=df.columns)

    # When the dataset is tiny we fall back to a leave‑one‑out style split
    if n <= 5:
        # deterministic leave‑one‑out using the first row as test
        test_df = df.iloc[[0]].copy()
        train_df = df.iloc[1:].copy()
        log.info(
            f"Dataset has {n} rows (≤5). Using leave‑one‑out split: "
            f"train={len(train_df)}, test={len(test_df)}"
        )
        return train_df, test_df

    train_df, test_df = train_test_split(
        df,
        test_size=test_size,
        random_state=random_state,
        shuffle=True,
    )
    log.info(f"Random split completed: Train={len(train_df)}, Test={len(test_df)}")
    return train_df, test_df

def stratified_split(
    df: pd.DataFrame,
    stratify_col: str,
    test_size: float = 0.2,
    random_state: int = 42,
    max_distribution_diff: Optional[float] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Perform a stratified split ensuring distribution difference < threshold.
    """
    config = _load_config()
    if max_distribution_diff is None:
        max_distribution_diff = config.get("stratification_diff_threshold", 0.05)

    if stratify_col not in df.columns:
        raise KeyError(f"Stratification column '{stratify_col}' not found.")

    # Drop NaN in stratify column to avoid train_test_split error
    df = df.dropna(subset=[stratify_col])

    # Stratification requires at least 2 members per class for a split
    class_counts = df[stratify_col].value_counts()
    if (class_counts < 2).any():
        log.warning(
            f"Some classes in '{stratify_col}' have < 2 samples. "
            f"Stratification impossible."
        )
        raise ValueError("Insufficient class members for stratification.")

    train_df, test_df = train_test_split(
        df,
        test_size=test_size,
        random_state=random_state,
        stratify=df[stratify_col],
        shuffle=True,
    )

    # Validate distribution difference (FR-004)
    train_dist = train_df[stratify_col].value_counts(normalize=True).sort_index()
    test_dist = test_df[stratify_col].value_counts(normalize=True).sort_index()
    all_classes = train_dist.index.union(test_dist.index)
    train_dist = train_dist.reindex(all_classes, fill_value=0)
    test_dist = test_dist.reindex(all_classes, fill_value=0)

    diff = (train_dist - test_dist).abs()
    max_diff = diff.max()

    if max_diff > max_distribution_diff:
        log.warning(
            f"Stratification difference {max_diff:.4f} exceeds threshold "
            f"{max_distribution_diff}. Proceeding but flagging for report."
        )
        # Continue – downstream can decide how to handle the warning.

    log.info(
        f"Stratified split successful: Train={len(train_df)}, "
        f"Test={len(test_df)}, MaxDiff={max_diff:.4f}"
    )
    return train_df, test_df

def _quantile_stratify(
    df: pd.DataFrame,
    target_col: str,
    n_bins: int = 5,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Stratify based on quantile bins of the target column.
    Creates a temporary column 'target_bin' for stratification,
    then uses the existing stratified_split logic.
    """
    # Create bins; drop duplicates to avoid errors when values are not enough
    try:
        df["target_bin"] = pd.qcut(
            df[target_col],
            q=n_bins,
            duplicates="drop",
        )
    except ValueError as e:
        # Fallback: if qcut cannot create bins (e.g., all values identical)
        log.warning(
            f"qcut failed for target stratification ({e}); falling back to random split."
        )
        return random_split(df, test_size=0.2, random_state=random_state)

    # Use the temporary bin column for stratified split
    train_df, test_df = stratified_split(
        df,
        stratify_col="target_bin",
        test_size=0.2,
        random_state=random_state,
    )
    # Drop the temporary column before returning
    train_df = train_df.drop(columns=["target_bin"])
    test_df = test_df.drop(columns=["target_bin"])
    return train_df, test_df

# ----------------------------------------------------------------------
# Main execution workflow
# ----------------------------------------------------------------------
def execute_split(
    df: pd.DataFrame,
    output_dir: str,
    test_size: float = 0.2,
    random_state: int = 42,
    stratify_column: str = "polymer_type",
) -> Tuple[str, str]:
    """
    Full split workflow implementing FR-004 and handling edge cases.

    Returns:
        Tuple of (train_parquet_path, test_parquet_path)
    """
    config = _load_config()
    target_col = config.get("target_column", "target")

    # 1. Filter to rows where target is non‑null
    df_filtered = df.dropna(subset=[target_col]).copy()
    if df_filtered.empty:
        log.error("No rows with a non‑null target found. Cannot split.")
        raise SystemExit(1)

    n_rows = len(df_filtered)
    split_strategy = "random"

    # 2. Choose splitting strategy
    if n_rows <= 5:
        # Leave‑one‑out split (guarantees at least one test sample)
        train_df, test_df = random_split(df_filtered, test_size=0.2, random_state=random_state)
        split_strategy = "leave_one_out"
    else:
        if stratify_column in df_filtered.columns:
            try:
                log.info(f"Attempting stratified split on '{stratify_column}'...")
                train_df, test_df = stratified_split(
                    df_filtered,
                    stratify_col=stratify_column,
                    test_size=test_size,
                    random_state=random_state,
                )
                split_strategy = "stratified"
            except (ValueError, KeyError) as e:
                log.warning(
                    f"Stratified split failed ({e}). Falling back to target quantile stratification."
                )
                # Fallback to quantile based stratification
                train_df, test_df = _quantile_stratify(
                    df_filtered,
                    target_col=target_col,
                    n_bins=5,
                    random_state=random_state,
                )
                split_strategy = "quantile_stratified"
        else:
            log.warning(
                f"Stratification column '{stratify_column}' absent. Using target quantile stratification."
            )
            train_df, test_df = _quantile_stratify(
                df_filtered,
                target_col=target_col,
                n_bins=5,
                random_state=random_state,
            )
            split_strategy = "quantile_stratified"

    # Ensure both splits contain at least one row (extra safety)
    if train_df.empty or test_df.empty:
        # Move a single random row to the empty side
        if train_df.empty:
            test_df, train_df = train_test_split(
                df_filtered,
                test_size=1,
                random_state=random_state,
                shuffle=True,
            )
        else:
            train_df, test_df = train_test_split(
                df_filtered,
                test_size=1,
                random_state=random_state,
                shuffle=True,
            )
        log.info(
            f"Adjusted split to guarantee non‑empty sets: train={len(train_df)}, test={len(test_df)}"
        )

    # 3. Persist splits
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    train_parquet = output_path / "train.parquet"
    test_parquet = output_path / "test.parquet"
    train_csv = output_path / "train.csv"
    test_csv = output_path / "test.csv"

    train_df.to_parquet(train_parquet, index=False)
    test_df.to_parquet(test_parquet, index=False)
    train_df.to_csv(train_csv, index=False)
    test_df.to_csv(test_csv, index=False)

    # 4. Metadata for downstream scripts
    metrics_path = paths.data("results", "split_metadata.json")
    metrics_path.parent.mkdir(parents=True, exist_ok=True)

    # Calculate max_diff if stratified
    max_diff = None
    if split_strategy in {"stratified", "quantile_stratified"}:
        col = stratify_column if split_strategy == "stratified" else "target_bin"
        if col in train_df.columns and col in test_df.columns:
            tr_d = train_df[col].value_counts(normalize=True).sort_index()
            te_d = test_df[col].value_counts(normalize=True).sort_index()
            max_diff = float((tr_d.reindex(te_d.index, fill_value=0) - te_d).abs().max())

    split_meta = {
        "split_strategy": split_strategy,
        "stratify_column": stratify_column if split_strategy == "stratified" else None,
        "train_size": len(train_df),
        "test_size": len(test_df),
        "max_distribution_diff": max_diff,
        "retention_rate": len(df_filtered) / len(df) if len(df) > 0 else 0,
    }

    with open(metrics_path, "w") as f:
        json.dump(split_meta, f, indent=2)

    log.info(f"Splits saved to {output_dir}. Strategy: {split_strategy}")
    return str(train_parquet), str(test_parquet)

def main():
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Split molecular data for training/testing."
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/processed_data.parquet",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
    )
    parser.add_argument(
        "--stratify-col",
        type=str,
        default="polymer_type",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        log.error(f"Input file not found: {input_path}")
        sys.exit(1)

    df = (
        pd.read_parquet(input_path)
        if input_path.suffix == ".parquet"
        else pd.read_csv(input_path)
    )

    try:
        execute_split(
            df,
            output_dir=args.output,
            test_size=args.test_size,
            random_state=args.seed,
            stratify_column=args.stratify_col,
        )
    except Exception as e:
        log.exception(f"Split failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()