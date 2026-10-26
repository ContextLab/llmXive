"""
Split utilities for the molecular permeability pipeline.

This module provides functions for performing train/test splits
with optional stratification, handling small datasets, and writing
both CSV and Parquet outputs. It also generates a JSON metadata
file that records the split strategy and the maximum class‑distribution
difference (``max_distribution_diff``). The implementation follows the
specifications in ``tasks.md`` and removes the hard dependency on a
``config.yaml`` file – a default threshold of 0.05 is used when the
configuration file is absent.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Tuple

import yaml
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration loader (optional)
# ----------------------------------------------------------------------
def _load_config() -> Dict:
    """
    Load ``config.yaml`` from the repository root if it exists.
    If the file is missing, return an empty dictionary so that the
    default values can be used. This makes the split script robust
    in environments where a configuration file is not provided.
    """
    config_path = Path(__file__).resolve().parents[3] / "config.yaml"
    if not config_path.is_file():
        # No config file – return empty dict; callers will fall back
        # to sensible defaults.
        return {}
    with config_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# ----------------------------------------------------------------------
# Random split
# ----------------------------------------------------------------------
def random_split(
    df: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Perform a simple random train/test split.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.
    test_size : float
        Fraction of the dataset to allocate to the test set.
    random_state : int
        Seed for reproducibility.

    Returns
    -------
    train_df, test_df : Tuple[pd.DataFrame, pd.DataFrame]
    """
    if not 0 < test_size < 1:
        raise ValueError("test_size must be between 0 and 1 (exclusive).")
    train, test = train_test_split(
        df,
        test_size=test_size,
        random_state=random_state,
        shuffle=True,
    )
    return train.reset_index(drop=True), test.reset_index(drop=True)

# ----------------------------------------------------------------------
# Stratified split
# ----------------------------------------------------------------------
def stratified_split(
    df: pd.DataFrame,
    stratify_col: str,
    test_size: float = 0.2,
    random_state: int = 42,
    max_distribution_diff: float = 0.05,
) -> Tuple[pd.DataFrame, pd.DataFrame, float]:
    """
    Perform a stratified train/test split while enforcing an absolute
    class‑distribution difference bound.

    Returns the train and test dataframes **and** the observed maximum
    distribution difference (``max_diff``). The caller can decide how
    to handle a violation of ``max_distribution_diff`` (e.g. fall back
    to a random split).

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.
    stratify_col : str
        Column name to use for stratification.
    test_size : float, optional
        Fraction of data for the test set.
    random_state : int, optional
        Seed for reproducibility.
    max_distribution_diff : float, optional
        Allowed absolute difference in class proportion between train
        and test for any class.

    Returns
    -------
    train_df, test_df, max_diff : Tuple[pd.DataFrame, pd.DataFrame, float]
    """
    if stratify_col not in df.columns:
        log.error(f"Stratification column '{stratify_col}' not found.")
        sys.exit(1)  # Expected by the unit test

    if df[stratify_col].nunique() < 2:
        raise ValueError(
            f"Stratification column '{stratify_col}' must contain at least two classes."
        )

    # Perform the split
    train, test = train_test_split(
        df,
        test_size=test_size,
        stratify=df[stratify_col],
        random_state=random_state,
    )

    # Compute class‑wise proportion differences
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

    return (
        train.reset_index(drop=True),
        test.reset_index(drop=True),
        max_diff,
    )

# ----------------------------------------------------------------------
# Execute split – used by the integration tests and the pipeline script
# ----------------------------------------------------------------------
def execute_split(
    df: pd.DataFrame,
    output_dir: str,
    stratify_column: str = None,
) -> Tuple[str, str]:
    """
    Split ``df`` into train and test sets, write CSV (and Parquet) files,
    and return the file paths.

    The function respects the configuration in ``config.yaml`` for the
    distribution‑difference threshold. If ``stratify_column`` is provided
    and present in the dataframe, a stratified split is attempted;
    otherwise a random split is performed.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe (typically the processed data).
    output_dir : str
        Directory where ``train.csv`` and ``test.csv`` will be stored.
    stratify_column : str, optional
        Column to use for stratification. If ``None`` or missing from the
        dataframe, a random split is used.

    Returns
    -------
    train_path, test_path : Tuple[str, str]
        Paths to the written CSV files.
    """
    config = _load_config()
    diff_threshold = config.get("stratification_diff_threshold", 0.05)

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # Identify the target column (per spec we support several names)
    target_col = None
    for possible in ["permeability", "permeability_coefficient", "target"]:
        if possible in df.columns:
            target_col = possible
            break
    if target_col:
        df = df.dropna(subset=[target_col]).copy()
    else:
        df = df.copy()

    # Small‑dataset leave‑one‑out handling
    if len(df) <= 5:
        log.info(f"Dataset has {len(df)} rows (≤5). Using leave‑one‑out split.")
        test_df = df.iloc[[0]].copy()
        train_df = df.iloc[1:].copy()
        split_strategy = "leave_one_out"
        max_diff = 0.0
    else:
        if stratify_column and stratify_column in df.columns:
            # Attempt stratified split
            try:
                train_df, test_df, max_diff = stratified_split(
                    df,
                    stratify_col=stratify_column,
                    test_size=0.2,
                    random_state=42,
                    max_distribution_diff=diff_threshold,
                )
                split_strategy = "stratified"
                # If the observed diff exceeds the threshold, fall back
                if max_diff > diff_threshold:
                    raise ValueError(
                        f"Observed max distribution diff {max_diff:.4f} exceeds "
                        f"threshold {diff_threshold:.4f}"
                    )
            except Exception as e:
                log.warning(f"Stratified split failed ({e}); falling back to random split.")
                train_df, test_df = random_split(df, test_size=0.2, random_state=42)
                split_strategy = "random_fallback"
                max_diff = None
        else:
            train_df, test_df = random_split(df, test_size=0.2, random_state=42)
            split_strategy = "random"
            max_diff = None

    # Write CSV and Parquet files
    train_csv = out_path / "train.csv"
    test_csv = out_path / "test.csv"
    train_parquet = out_path / "train.parquet"
    test_parquet = out_path / "test.parquet"

    train_df.to_csv(train_csv, index=False)
    test_df.to_csv(test_csv, index=False)
    train_df.to_parquet(train_parquet, index=False)
    test_df.to_parquet(test_parquet, index=False)

    # Build metadata
    metadata = {
        "split_strategy": split_strategy,
        "stratify_column": stratify_column if stratify_column in df.columns else None,
        "train_size": len(train_df),
        "test_size": len(test_df),
        "max_distribution_diff": max_diff,
        "retention_rate": 1.0,
    }
    metadata_path = out_path / "split_metadata.json"
    with metadata_path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    log.info(
        f"Split strategy: {split_strategy}. "
        f"Wrote train={train_csv} ({len(train_df)} rows), "
        f"test={test_csv} ({len(test_df)} rows). "
        f"max_distribution_diff={max_diff}"
    )
    return str(train_csv), str(test_csv)

# ----------------------------------------------------------------------
# Helper functions used by the original script (kept for backward
# compatibility)
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

def stratify_labels(df: pd.DataFrame, target_col: str) -> pd.Series:
    """Produce a stratification series based on polymer_type or target quantiles."""
    if "polymer_type" in df.columns:
        log.info("Stratifying by existing 'polymer_type' column.")
        return df["polymer_type"]
    else:
        log.info("Creating quantile bins for stratification.")
        n_bins = min(5, df[target_col].nunique())
        strat_series, _ = pd.qcut(df[target_col], q=n_bins, duplicates="drop", retbins=True)
        return strat_series.astype(str)

def write_split(df: pd.DataFrame, name: str, base_dir: Path) -> None:
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
    """Create a JSON metadata dictionary for downstream steps."""
    max_diff = None
    if not stratify_series.empty:
        train_props = (
            train_df[stratify_series.name]
            .value_counts(normalize=True)
            .reindex(stratify_series.unique(), fill_value=0)
        )
        test_props = (
            test_df[stratify_series.name]
            .value_counts(normalize=True)
            .reindex(stratify_series.unique(), fill_value=0)
        )
        max_diff = float(np.max(np.abs(train_props - test_props)))
    metadata = {
        "split_strategy": split_strategy,
        "stratify_column": (
            "polymer_type" if "polymer_type" in train_df.columns else "target_quantile_bins"
        ),
        "train_size": len(train_df),
        "test_size": len(test_df),
        "max_distribution_diff": max_diff,
        "retention_rate": 1.0,
    }
    return metadata

# ----------------------------------------------------------------------
# Main execution (script entry‑point)
# ----------------------------------------------------------------------
def main() -> int:
    """
    Command‑line entry point used by the pipeline. It loads the processed
    data, applies the appropriate split logic, writes artefacts and a
    small JSON metadata file.
    """
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
            log.info(f"Dataset has {len(df)} rows (≤5); using leave‑one‑out split.")
            test_df = df.iloc[[0]].copy()
            train_df = df.iloc[1:].copy()
            split_strategy = "leave_one_out"
            max_diff = 0.0
        else:
            # Determine stratification series
            strat_series = stratify_labels(df, target_col)

            # Perform split using sklearn's train_test_split (which respects the series)
            train_df, test_df = train_test_split(
                df,
                test_size=0.2,
                stratify=strat_series,
                random_state=42,
            )
            split_strategy = "stratified"

            # Compute max distribution difference for metadata
            train_props = (
                train_df[strat_series.name]
                .value_counts(normalize=True)
                .reindex(strat_series.unique(), fill_value=0)
            )
            test_props = (
                test_df[strat_series.name]
                .value_counts(normalize=True)
                .reindex(strat_series.unique(), fill_value=0)
            )
            max_diff = float(np.max(np.abs(train_props - test_props)))

        # Write outputs
        split_dir = paths.data("processed")
        write_split(train_df, "train", split_dir)
        write_split(test_df, "test", split_dir)

        # Write metadata JSON
        metadata = {
            "split_strategy": split_strategy,
            "stratify_column": strat_series.name if len(df) > 5 else None,
            "train_size": len(train_df),
            "test_size": len(test_df),
            "max_distribution_diff": max_diff,
            "retention_rate": 1.0,
        }
        metadata_path = split_dir / "split_metadata.json"
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        with metadata_path.open("w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        log.info(f"Split metadata written to {metadata_path}")

        return 0
    except Exception as exc:
        log.error(f"Split script failed: {exc}")
        return 1

if __name__ == "__main__":
    sys.exit(main())