"""
metadata_stats.py - Compute tabular feature statistics for MulTaBench datasets.

This module calculates cardinality, missingness, sparsity, and variance for
all tabular features across ALL available datasets.

Output: data/processed/metadata_stats_summary.csv
Columns: dataset_id, cardinality, missingness, sparsity, variance
"""

import os
import sys
import json
import hashlib
from datetime import datetime
from pathlib import Path
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import argparse

# Project root resolution
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"

# Ensure output directory exists
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def load_dataset_list() -> List[Dict[str, Any]]:
    """
    Load the list of available datasets from the project configuration or manifest.
    Falls back to scanning data/ for known dataset identifiers if no manifest exists.
    """
    manifest_path = DATA_DIR / "dataset_manifest.json"
    if manifest_path.exists():
        with open(manifest_path, 'r') as f:
            data = json.load(f)
            # Expecting a list of dicts with 'dataset_id' and 'path' or 'name'
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "datasets" in data:
                return data["datasets"]

    # Fallback: Scan data/raw or data/processed for known dataset patterns
    # MulTaBench datasets are typically stored in specific directories
    raw_dir = DATA_DIR / "raw"
    if raw_dir.exists():
        datasets = []
        for item in raw_dir.iterdir():
            if item.is_dir() or (item.suffix in ['.parquet', '.csv', '.json']):
                # Heuristic: assume directory name or stem is dataset_id
                dataset_id = item.name
                if item.is_dir():
                    # Check for common data files inside
                    parquet_files = list(item.glob("*.parquet"))
                    csv_files = list(item.glob("*.csv"))
                    if parquet_files or csv_files:
                        datasets.append({"dataset_id": dataset_id, "path": str(item)})
                else:
                    datasets.append({"dataset_id": dataset_id, "path": str(item)})
        return datasets

    # If no data found, raise an error to fail loudly
    raise FileNotFoundError(
        f"No dataset manifest found at {manifest_path} and no datasets found in {DATA_DIR}. "
        "Please ensure data has been ingested via T007/T008."
    )

def compute_feature_stats(df: pd.DataFrame) -> Dict[str, float]:
    """
    Compute cardinality, missingness, sparsity, and variance for tabular features.

    Args:
        df: Pandas DataFrame containing tabular features.

    Returns:
        Dictionary with aggregated stats:
        - cardinality: Average unique values per numeric column (log10 scaled for stability)
        - missingness: Fraction of total cells that are NaN
        - sparsity: Fraction of zero values in numeric columns
        - variance: Average variance of numeric columns
    """
    if df.empty:
        return {
            "cardinality": 0.0,
            "missingness": 1.0,
            "sparsity": 0.0,
            "variance": 0.0
        }

    # Select numeric columns for statistical analysis
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    categorical_cols = df.select_dtypes(exclude=[np.number]).columns

    # 1. Missingness (overall)
    total_cells = df.size
    missing_cells = df.isna().sum().sum()
    missingness = float(missing_cells / total_cells) if total_cells > 0 else 0.0

    # 2. Sparsity (fraction of zeros in numeric columns)
    sparsity = 0.0
    if len(numeric_cols) > 0:
        total_numeric = df[numeric_cols].size
        zero_count = (df[numeric_cols] == 0).sum().sum()
        sparsity = float(zero_count / total_numeric) if total_numeric > 0 else 0.0

    # 3. Variance (average variance of numeric columns)
    variance_sum = 0.0
    valid_var_count = 0
    for col in numeric_cols:
        col_data = df[col].dropna()
        if len(col_data) > 1:
            var_val = col_data.var()
            if not np.isnan(var_val):
                variance_sum += var_val
                valid_var_count += 1
    avg_variance = variance_sum / valid_var_count if valid_var_count > 0 else 0.0

    # 4. Cardinality (average unique values per column, log-scaled)
    # For numeric: count unique values. For categorical: count unique values.
    # We use log10(unique_count + 1) to handle large cardinalities and avoid inf
    cardinality_sum = 0.0
    valid_card_count = 0
    all_cols = list(numeric_cols) + list(categorical_cols)
    for col in all_cols:
        unique_count = df[col].nunique()
        # Log scale to prevent skew from high-cardinality IDs
        log_unique = np.log10(unique_count + 1)
        cardinality_sum += log_unique
        valid_card_count += 1
    avg_cardinality = cardinality_sum / valid_card_count if valid_card_count > 0 else 0.0

    return {
        "cardinality": float(avg_cardinality),
        "missingness": float(missingness),
        "sparsity": float(sparsity),
        "variance": float(avg_variance)
    }

def process_single_dataset(dataset_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Process a single dataset to compute metadata statistics.

    Args:
        dataset_info: Dict with 'dataset_id' and 'path' (or other locators).

    Returns:
        Dict with dataset_id and computed stats, or None if processing fails.
    """
    dataset_id = dataset_info.get("dataset_id")
    dataset_path = dataset_info.get("path")

    if not dataset_id or not dataset_path:
        print(f"Warning: Skipping dataset entry missing id or path: {dataset_info}")
        return None

    path_obj = Path(dataset_path)

    # Try to load as parquet first, then csv
    df = None
    if path_obj.suffix == '.parquet':
        try:
            df = pd.read_parquet(path_obj)
        except Exception as e:
            print(f"Error reading parquet {path_obj}: {e}")
            return None
    elif path_obj.suffix == '.csv':
        try:
            df = pd.read_csv(path_obj)
        except Exception as e:
            print(f"Error reading csv {path_obj}: {e}")
            return None
    elif path_obj.is_dir():
        # Look for a primary data file inside the directory
        parquet_files = list(path_obj.glob("*.parquet"))
        csv_files = list(path_obj.glob("*.csv"))
        if parquet_files:
            try:
                df = pd.read_parquet(parquet_files[0])
            except Exception as e:
                print(f"Error reading parquet in dir {path_obj}: {e}")
                return None
        elif csv_files:
            try:
                df = pd.read_csv(csv_files[0])
            except Exception as e:
                print(f"Error reading csv in dir {path_obj}: {e}")
                return None
        else:
            print(f"Warning: No data files found in directory {path_obj}")
            return None
    else:
        print(f"Warning: Unsupported file type or missing path: {path_obj}")
        return None

    if df is None or df.empty:
        print(f"Warning: Empty or failed to load dataset {dataset_id}")
        return None

    # Compute stats
    stats = compute_feature_stats(df)

    return {
        "dataset_id": dataset_id,
        "cardinality": stats["cardinality"],
        "missingness": stats["missingness"],
        "sparsity": stats["sparsity"],
        "variance": stats["variance"]
    }

def save_summary_csv(results: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save the computed statistics to a single summary CSV file.

    Args:
        results: List of dicts containing dataset_id and stats.
        output_path: Path to the output CSV file.
    """
    if not results:
        print("Warning: No results to save.")
        # Create an empty file with headers
        df_empty = pd.DataFrame(columns=["dataset_id", "cardinality", "missingness", "sparsity", "variance"])
        df_empty.to_csv(output_path, index=False)
        return

    df_results = pd.DataFrame(results)
    # Ensure column order
    cols = ["dataset_id", "cardinality", "missingness", "sparsity", "variance"]
    df_results = df_results[cols]
    df_results.to_csv(output_path, index=False)
    print(f"Saved metadata stats summary to {output_path}")

def main() -> None:
    """
    Main entry point: Load all datasets, compute stats, and save summary.
    """
    print("Starting metadata statistics computation for ALL available datasets...")

    # Load dataset list
    try:
        datasets = load_dataset_list()
        print(f"Found {len(datasets)} datasets to process.")
    except FileNotFoundError as e:
        print(f"Critical Error: {e}")
        sys.exit(1)

    results = []
    for ds_info in datasets:
        dataset_id = ds_info.get("dataset_id", "unknown")
        print(f"Processing dataset: {dataset_id}...")
        try:
            result = process_single_dataset(ds_info)
            if result:
                results.append(result)
                print(f"  -> Stats computed for {dataset_id}")
            else:
                print(f"  -> Skipped {dataset_id} (no data or error)")
        except Exception as e:
            print(f"  -> ERROR processing {dataset_id}: {e}")
            # Fail loudly on real data processing errors
            raise

    if not results:
        print("Warning: No datasets were successfully processed. Creating empty summary.")

    output_path = PROCESSED_DIR / "metadata_stats_summary.csv"
    save_summary_csv(results, output_path)

    print("Metadata statistics computation complete.")

if __name__ == "__main__":
    main()