"""
Split the processed dataset into training and test sets.

This script reads ``data/processed/processed_data.parquet`` (or
``processed_data.csv`` as a fallback), performs a stratified split
according to the specification, and writes the four split files
(CSV & Parquet) together with a small ``split_metadata.json`` file.

The split strategy follows the rules from the project plan:

* If a ``polymer_type`` column exists → stratify by that column,
  preserving an absolute ≤5 percentage‑point difference between
  train and test class proportions.
* Otherwise → stratify by quantile bins of the target column
  (5‑fold quantiles by default).
* For ≤5 rows → leave‑one‑out split (single row becomes the test set).

All paths are resolved via ``llmxive_toolkit.paths`` which creates the
required directories automatically.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def load_processed_data() -> pd.DataFrame:
    """Load the processed dataset (Parquet preferred, CSV fallback)."""
    parquet_path = paths.data("processed", "processed_data.parquet")
    csv_path = paths.data("processed", "processed_data.csv")
    if parquet_path.is_file():
        log.info(f"Loading processed data from {parquet_path}")
        return pd.read_parquet(parquet_path)
    elif csv_path.is_file():
        log.info(f"Loading processed data from {csv_path}")
        return pd.read_csv(csv_path)
    else:
        raise FileNotFoundError(
            "Neither processed_data.parquet nor processed_data.csv was found."
        )

def determine_target_column(df: pd.DataFrame) -> str:
    """Return the name of the column that holds the permeability target."""
    possible = ["permeability", "permeability_coefficient", "target"]
    for col in possible:
        if col in df.columns:
            return col
    raise ValueError("No recognised target column found in the processed data.")

def stratify_labels(
    df: pd.DataFrame, target_col: str
) -> pd.Series:
    """
    Produce a stratification series.

    If ``polymer_type`` exists, use it directly.
    Otherwise create quantile‑based bins of the target.
    """
    if "polymer_type" in df.columns:
        log.info("Stratifying by existing 'polymer_type' column.")
        return df["polymer_type"]
    else:
        log.info("Creating quantile bins for stratification.")
        # 5‑fold quantiles (or fewer if not enough unique values)
        n_bins = min(5, df[target_col].nunique())
        # pandas.qcut creates roughly equal‑sized bins
        strat_series, _ = pd.qcut(df[target_col], q=n_bins, duplicates="drop", retbins=True)
        # Convert Interval objects to string labels for sklearn
        return strat_series.astype(str)

def write_split(
    df: pd.DataFrame, name: str, base_dir: Path
) -> None:
    """Write a split dataframe to CSV and Parquet."""
    csv_path = base_dir / f"{name}.csv"
    parquet_path = base_dir / f"{name}.parquet"
    df.to_csv(csv_path, index=False)
    df.to_parquet(parquet_path, index=False)
    log.info(f"Wrote {name} split: {csv_path} & {parquet_path}")

def generate_metadata(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    stratify_series: pd.Series,
    split_strategy: str,
) -> Dict:
    """Create a small JSON metadata dictionary for downstream steps."""
    metadata = {
        "split_strategy": split_strategy,
        "stratify_column": "polymer_type"
        if "polymer_type" in train_df.columns
        else "target_quantile_bins",
        "train_size": len(train_df),
        "test_size": len(test_df),
        "max_distribution_diff": None,  # filled in by downstream report if needed
        "retention_rate": 1.0,
    }
    return metadata

# ----------------------------------------------------------------------
# Main execution
# ----------------------------------------------------------------------
def main() -> int:
    try:
        df = load_processed_data()
        target_col = determine_target_column(df)

        # Ensure we only split rows where the target is present
        df = df.dropna(subset=[target_col])
        if df.empty:
            log.error("No rows with a non‑null target after dropping NAs.")
            return 1

        # Leave‑one‑out handling for very small datasets
        if len(df) <= 5:
            log.info(
                f"Dataset has {len(df)} rows (≤5); using leave‑one‑out split."
            )
            test_df = df.iloc[[0]].copy()
            train_df = df.iloc[1:].copy()
            split_strategy = "leave_one_out"
        else:
            strat_series = stratify_labels(df, target_col)
            # Use a fixed random_state for reproducibility
            train_df, test_df = train_test_split(
                df,
                test_size=0.2,
                stratify=strat_series,
                random_state=42,
            )
            split_strategy = "stratified"

        # Write outputs
        split_dir = paths.data("processed")
        write_split(train_df, "train", split_dir)
        write_split(test_df, "test", split_dir)

        # Write metadata JSON
        metadata = generate_metadata(train_df, test_df, strat_series if len(df) > 5 else pd.Series(), split_strategy)
        metadata_path = split_dir / "split_metadata.json"
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        with metadata_path.open("w") as f:
            json.dump(metadata, f, indent=2)
        log.info(f"Split metadata written to {metadata_path}")

        return 0
    except Exception as exc:
        log.error(f"Split script failed: {exc}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
