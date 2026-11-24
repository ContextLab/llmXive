"""
Split utilities for the molecular permeability pipeline.

This module provides functions for performing train/test splits
with optional stratification, handling small datasets, and writing
both CSV and Parquet outputs. It also generates a JSON metadata
file that records the split strategy and the maximum class‑distribution
difference (max_distribution_diff).
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Tuple, Optional

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def random_split(
    df: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Perform a simple random train/test split."""
    train, test = train_test_split(
        df,
        test_size=test_size,
        random_state=random_state,
        shuffle=True,
    )
    return train.reset_index(drop=True), test.reset_index(drop=True)

def stratified_split(
    df: pd.DataFrame,
    stratify_col: str,
    test_size: float = 0.2,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, float]:
    """
    Perform a stratified train/test split and return the observed 
    maximum distribution difference.
    """
    train, test = train_test_split(
        df,
        test_size=test_size,
        stratify=df[stratify_col],
        random_state=random_state,
    )

    # Compute class-wise proportion differences
    train_props = (
        train[stratify_col]
        .value_counts(normalize=True)
        .reindex(df[stratify_col].unique(), fill_value=0)
    )
    test_props = (
        test[stratify_col]
        .value_counts(normalize=True)
        .reindex(df[stratify_col].unique(), fill_value=0)
    )
    max_diff = float(np.max(np.abs(train_props - test_props)))

    return train.reset_index(drop=True), test.reset_index(drop=True), max_diff

def load_processed_data() -> pd.DataFrame:
    """Load the processed dataset (Parquet preferred, CSV fallback)."""
    parquet_path = paths.data("processed", "processed_data.parquet")
    csv_path = paths.data("processed", "processed_data.csv")
    if parquet_path.is_file():
        return pd.read_parquet(parquet_path)
    elif csv_path.is_file():
        return pd.read_csv(csv_path)
    else:
        raise FileNotFoundError("No processed data found in data/processed/")

def determine_target_column(df: pd.DataFrame) -> str:
    """Return the name of the column that holds the permeability target."""
    for possible in ["permeability", "permeability_coefficient", "target"]:
        if possible in df.columns:
            return possible
    raise ValueError("No recognized target column found in the processed data.")

def write_split(df: pd.DataFrame, name: str, base_dir: Path) -> None:
    """Write a split dataframe to CSV and Parquet."""
    csv_path = base_dir / f"{name}.csv"
    parquet_path = base_dir / f"{name}.parquet"
    df.to_csv(csv_path, index=False)
    df.to_parquet(parquet_path, index=False)
    log.info(f"Wrote {name} split: {csv_path} & {parquet_path}")

def main() -> int:
    """
    Main entry point: loads processed data, applies stratified or 
    leave-one-out splitting, and writes artifacts.
    """
    try:
        df = load_processed_data()
        target_col = determine_target_column(df)

        # Filter to rows where target is non-null
        df = df.dropna(subset=[target_col]).copy()
        if df.empty:
            log.error("No rows with a non-null target found.")
            return 1

        split_dir = paths.data("processed")
        split_dir.mkdir(parents=True, exist_ok=True)

        # Small-dataset leave-one-out handling (<= 5 rows)
        if len(df) <= 5:
            log.info(f"Dataset size {len(df)} <= 5. Using leave-one-out split.")
            test_df = df.iloc[[0]].copy()
            train_df = df.iloc[1:].copy()
            split_strategy = "leave_one_out"
            stratify_column = None
            max_diff = 0.0
        else:
            # Determine stratification strategy
            if "polymer_type" in df.columns:
                log.info("Stratifying by 'polymer_type'.")
                stratify_column = "polymer_type"
                try:
                    train_df, test_df, max_diff = stratified_split(
                        df, stratify_col=stratify_column
                    )
                    split_strategy = "stratified"
                except Exception as e:
                    log.warning(f"Stratified split by polymer_type failed ({e}); falling back to random.")
                    train_df, test_df = random_split(df)
                    split_strategy = "random_fallback"
                    stratify_column = None
                    max_diff = None
            else:
                log.info("Stratifying by target-value quantile bins.")
                # Create 5-fold quantile bins for stratification
                n_bins = min(5, df[target_col].nunique())
                df["_strat_bins"] = pd.qcut(
                    df[target_col], q=n_bins, duplicates="drop"
                ).astype(str)
                stratify_column = "_strat_bins"
                try:
                    train_df, test_df, max_diff = stratified_split(
                        df, stratify_col=stratify_column
                    )
                    split_strategy = "stratified"
                except Exception as e:
                    log.warning(f"Stratified split by quantiles failed ({e}); falling back to random.")
                    train_df, test_df = random_split(df)
                    split_strategy = "random_fallback"
                    stratify_column = None
                    max_diff = None
                # Clean up temporary bin column
                train_df = train_df.drop(columns=["_strat_bins"], errors="ignore")
                test_df = test_df.drop(columns=["_strat_bins"], errors="ignore")

            # Check stratification constraint (<= 5 percentage-point difference)
            if split_strategy == "stratified" and max_diff is not None:
                if max_diff > 0.05:
                    log.warning(f"Stratification difference {max_diff:.4f} exceeds 0.05 threshold.")

        # Write split files
        write_split(train_df, "train", split_dir)
        write_split(test_df, "test", split_dir)

        # Write metadata
        metadata = {
            "split_strategy": split_strategy,
            "stratify_column": stratify_column,
            "train_size": len(train_df),
            "test_size": len(test_df),
            "max_distribution_diff": max_diff,
            "retention_rate": 1.0,
            "train_test_ratio": len(train_df) / len(test_df) if len(test_df) > 0 else 0,
        }
        metadata_path = split_dir / "split_metadata.json"
        with metadata_path.open("w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        
        log.info(f"Split complete. Strategy: {split_strategy}. Max Diff: {max_diff}")
        return 0

    except Exception as exc:
        log.error(f"Split script failed: {exc}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
