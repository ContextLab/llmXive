"""
Metadata Statistics Computation Module.

Computes cardinality, missingness, sparsity, and variance for tabular datasets.
"""
import os
import sys
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

# Import logging utilities from the project's utils
try:
    from utils.logging import get_logger, log_info, log_warning, log_error
except ImportError:
    # Fallback if utils is not in path during direct execution
    import logging
    def get_logger(name):
        return logging.getLogger(name)
    def log_info(logger, msg): logger.info(msg)
    def log_warning(logger, msg): logger.warning(msg)
    def log_error(logger, msg): logger.error(msg)

logger = get_logger(__name__)

# Constants
RAW_DATA_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
OUTPUT_FILE = PROCESSED_DIR / "metadata_stats_summary.csv"
VAR_THRESHOLD = 1e-9  # Threshold for considering variance as zero

def load_dataset_list() -> List[str]:
    """
    Scans data/raw/ for available dataset files (CSV/Parquet) and returns their IDs.
    Assumes files are named like {dataset_id}.csv or {dataset_id}.parquet.
    """
    if not RAW_DATA_DIR.exists():
        log_error(logger, f"Raw data directory {RAW_DATA_DIR} does not exist.")
        return []

    files = list(RAW_DATA_DIR.glob("*.csv")) + list(RAW_DATA_DIR.glob("*.parquet"))
    if not files:
        log_warning(logger, f"No CSV or Parquet files found in {RAW_DATA_DIR}.")
        return []

    dataset_ids = []
    for f in files:
        # Extract ID by removing extension
        dataset_id = f.stem
        dataset_ids.append(dataset_id)
    
    log_info(logger, f"Found {len(dataset_ids)} datasets: {dataset_ids}")
    return dataset_ids

def load_raw_tabular_data(dataset_id: str) -> Optional[pd.DataFrame]:
    """
    Loads a single dataset by ID from data/raw/.
    """
    csv_path = RAW_DATA_DIR / f"{dataset_id}.csv"
    parquet_path = RAW_DATA_DIR / f"{dataset_id}.parquet"

    if csv_path.exists():
        try:
            return pd.read_csv(csv_path)
        except Exception as e:
            log_error(logger, f"Failed to load CSV {csv_path}: {e}")
            return None
    elif parquet_path.exists():
        try:
            return pd.read_parquet(parquet_path)
        except Exception as e:
            log_error(logger, f"Failed to load Parquet {parquet_path}: {e}")
            return None
    else:
        log_error(logger, f"No file found for dataset {dataset_id} in {RAW_DATA_DIR}.")
        return None

def compute_cardinality(df: pd.DataFrame, column: str) -> float:
    """Computes the number of unique values in a column."""
    if df[column].dtype == 'object' or df[column].dtype.name.startswith('category'):
        return df[column].nunique()
    else:
        # For numeric, count unique
        return df[column].nunique()

def compute_missingness(df: pd.DataFrame, column: str) -> float:
    """Computes the fraction of missing values in a column."""
    total = len(df)
    if total == 0:
        return 0.0
    missing = df[column].isna().sum()
    return float(missing / total)

def compute_sparsity(df: pd.DataFrame, column: str) -> float:
    """
    Computes sparsity (fraction of zeros) for numeric columns.
    Returns 0.0 for non-numeric columns.
    """
    if not np.issubdtype(df[column].dtype, np.number):
        return 0.0
    
    total = len(df)
    if total == 0:
        return 0.0
    
    zero_count = (df[column] == 0).sum()
    return float(zero_count / total)

def compute_variance(df: pd.DataFrame, column: str) -> float:
    """Computes the variance of a numeric column."""
    if not np.issubdtype(df[column].dtype, np.number):
        return 0.0
    
    return float(df[column].var())

def compute_feature_stats(df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    """
    Computes stats for all numeric columns in the dataframe.
    Returns a dict mapping column_name -> {cardinality, missingness, sparsity, variance}
    """
    stats = {}
    numeric_cols = df.select_dtypes(include=[np.number]).columns

    for col in numeric_cols:
        stats[col] = {
            "cardinality": float(compute_cardinality(df, col)),
            "missingness": float(compute_missingness(df, col)),
            "sparsity": float(compute_sparsity(df, col)),
            "variance": float(compute_variance(df, col))
        }
    return stats

def process_single_dataset(dataset_id: str) -> Optional[Dict[str, Any]]:
    """
    Processes a single dataset and returns aggregated stats.
    Aggregation logic:
    - Cardinality: Mean of column cardinalities
    - Missingness: Mean of column missingness
    - Sparsity: Mean of column sparsity
    - Variance: Mean of column variance
    """
    df = load_raw_tabular_data(dataset_id)
    if df is None:
        return None

    if df.empty:
        log_warning(logger, f"Dataset {dataset_id} is empty.")
        return {
            "dataset_id": dataset_id,
            "cardinality": 0.0,
            "missingness": 0.0,
            "sparsity": 0.0,
            "variance": 0.0
        }

    feature_stats = compute_feature_stats(df)
    if not feature_stats:
        # No numeric columns found
        log_warning(logger, f"Dataset {dataset_id} has no numeric columns.")
        return {
            "dataset_id": dataset_id,
            "cardinality": 0.0,
            "missingness": 0.0,
            "sparsity": 0.0,
            "variance": 0.0
        }

    # Aggregate across columns
    cardinality_vals = [s["cardinality"] for s in feature_stats.values()]
    missingness_vals = [s["missingness"] for s in feature_stats.values()]
    sparsity_vals = [s["sparsity"] for s in feature_stats.values()]
    variance_vals = [s["variance"] for s in feature_stats.values()]

    return {
        "dataset_id": dataset_id,
        "cardinality": float(np.mean(cardinality_vals)),
        "missingness": float(np.mean(missingness_vals)),
        "sparsity": float(np.mean(sparsity_vals)),
        "variance": float(np.mean(variance_vals))
    }

def save_summary_csv(results: List[Dict[str, Any]], output_path: Path):
    """Saves the aggregated results to a CSV file."""
    if not results:
        log_warning(logger, "No results to save.")
        return

    df_results = pd.DataFrame(results)
    # Ensure column order
    cols = ["dataset_id", "cardinality", "missingness", "sparsity", "variance"]
    df_results = df_results[cols]
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_results.to_csv(output_path, index=False)
    log_info(logger, f"Saved metadata stats summary to {output_path}")

def compute_all_stats() -> Path:
    """
    Main entry point to compute stats for ALL available datasets.
    Iterates through data/raw/, computes stats, and aggregates into one CSV.
    """
    log_info(logger, "Starting computation of metadata stats for all datasets.")
    
    dataset_ids = load_dataset_list()
    if not dataset_ids:
        log_error(logger, "No datasets found to process.")
        # Still create an empty file or exit? Task says write file.
        # Create empty header file to satisfy 'file exists' check
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(columns=["dataset_id", "cardinality", "missingness", "sparsity", "variance"]).to_csv(OUTPUT_FILE, index=False)
        return OUTPUT_FILE

    results = []
    for ds_id in dataset_ids:
        log_info(logger, f"Processing dataset: {ds_id}")
        stats = process_single_dataset(ds_id)
        if stats:
            results.append(stats)
        else:
            log_warning(logger, f"Skipped dataset {ds_id} due to load failure.")

    save_summary_csv(results, OUTPUT_FILE)
    log_info(logger, "Metadata stats computation completed.")
    return OUTPUT_FILE

def main():
    """CLI entry point."""
    log_info(logger, "Running metadata stats computation via CLI.")
    output_path = compute_all_stats()
    print(f"Output written to: {output_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
