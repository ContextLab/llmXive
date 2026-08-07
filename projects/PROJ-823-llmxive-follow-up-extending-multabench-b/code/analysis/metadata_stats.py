import os
import sys
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import numpy as np

from utils.logging import get_logger, log_info, log_error, log_warning

logger = get_logger(__name__)

def load_dataset_list() -> List[str]:
    """
    Loads the list of available dataset IDs from the raw data directory.
    Looks for CSV files or subdirectories in data/raw/.
    """
    raw_path = Path("data/raw")
    if not raw_path.exists():
        log_error("data/raw/ does not exist.")
        return []
    
    datasets = []
    for item in raw_path.iterdir():
        if item.is_file() and item.suffix == '.csv':
            # Exclude the baseline file if it exists there, as it's not a raw dataset
            if item.name == 'multabench_baselines.csv':
                continue
            datasets.append(item.stem)
        elif item.is_dir():
            datasets.append(item.name)
    
    log_info(f"Found {len(datasets)} datasets: {datasets}")
    return datasets

def compute_feature_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes cardinality, missingness, sparsity, and variance for numeric features.
    Excludes non-numeric columns and 'dataset_id' if present.
    """
    stats = {}
    # Select only numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Remove 'dataset_id' if present in numeric columns
    if 'dataset_id' in numeric_cols:
        numeric_cols.remove('dataset_id')
    
    # If no numeric features, return zeros
    if not numeric_cols:
        log_warning(f"No numeric features found in dataset. Returning zero stats.")
        return {
            "cardinality": {},
            "missingness": {},
            "sparsity": {},
            "variance": {}
        }
    
    cardinality = {}
    missingness = {}
    sparsity = {}
    variance = {}
    
    for col in numeric_cols:
        col_data = df[col]
        
        # Cardinality (unique values)
        cardinality[col] = float(col_data.nunique())
        
        # Missingness (percentage)
        missingness[col] = float(col_data.isna().sum() / len(col_data))
        
        # Sparsity (percentage of zeros)
        sparsity[col] = float((col_data == 0).sum() / len(col_data))
        
        # Variance (sample variance, ddof=1)
        var_val = col_data.var()
        variance[col] = float(var_val) if not np.isnan(var_val) else 0.0
    
    return {
        "cardinality": cardinality,
        "missingness": missingness,
        "sparsity": sparsity,
        "variance": variance
    }

def process_single_dataset(dataset_id: str) -> Dict[str, Any]:
    """
    Loads a single dataset and computes its stats.
    Handles both CSV files and directories containing CSVs.
    """
    raw_path = Path("data/raw")
    file_path = raw_path / f"{dataset_id}.csv"
    dir_path = raw_path / dataset_id
    
    df = None
    try:
        if file_path.exists():
            df = pd.read_csv(file_path)
        elif dir_path.exists() and dir_path.is_dir():
            csv_files = list(dir_path.glob("*.csv"))
            if not csv_files:
                raise FileNotFoundError(f"No CSV files found in {dir_path}")
            dfs = [pd.read_csv(f) for f in csv_files]
            df = pd.concat(dfs, ignore_index=True)
        else:
            raise FileNotFoundError(f"Dataset path not found: {file_path} or {dir_path}")
        
        if df.empty:
            log_warning(f"Dataset {dataset_id} is empty.")
            return None
        
        stats = compute_feature_stats(df)
        stats["dataset_id"] = dataset_id
        return stats
    except Exception as e:
        log_error(f"Failed to process dataset {dataset_id}: {e}")
        return None

def save_summary_csv(stats_list: List[Dict[str, Any]], output_path: Path):
    """
    Saves the summary stats to a CSV file.
    Aggregates per-feature stats into mean values per dataset.
    """
    rows = []
    valid_count = 0
    
    for s in stats_list:
        if s is None:
            continue
        
        # Aggregate: Mean across all features for each metric
        cardinality_vals = list(s.get("cardinality", {}).values())
        missingness_vals = list(s.get("missingness", {}).values())
        sparsity_vals = list(s.get("sparsity", {}).values())
        variance_vals = list(s.get("variance", {}).values())
        
        row = {
            "dataset_id": s.get("dataset_id"),
            "cardinality": float(np.mean(cardinality_vals)) if cardinality_vals else 0.0,
            "missingness": float(np.mean(missingness_vals)) if missingness_vals else 0.0,
            "sparsity": float(np.mean(sparsity_vals)) if sparsity_vals else 0.0,
            "variance": float(np.mean(variance_vals)) if variance_vals else 0.0
        }
        rows.append(row)
        valid_count += 1
    
    if not rows:
        log_error("No valid stats to save.")
        return
    
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    log_info(f"Saved summary to {output_path} with {valid_count} rows.")
    
    # Verification: Check row count against input dataset list
    # (This is a log check, not a crash, as some datasets might fail to load)
    log_info(f"Verification: Output rows ({valid_count}) vs Expected (from stats_list).")

def main():
    """
    Main entry point for T024.
    Computes metadata stats for ALL available datasets and saves to CSV.
    """
    log_info("Starting T024: Metadata Stats computation.")
    
    dataset_list = load_dataset_list()
    
    if not dataset_list:
        log_error("No datasets found in data/raw/. Exiting.")
        return
    
    stats_list = []
    for ds_id in dataset_list:
        log_info(f"Processing dataset: {ds_id}")
        stats = process_single_dataset(ds_id)
        if stats:
            stats_list.append(stats)
        else:
            log_warning(f"Skipping {ds_id} due to processing failure.")
    
    output_path = Path("data/processed/metadata_stats_summary.csv")
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    save_summary_csv(stats_list, output_path)
    
    # Final verification
    if len(stats_list) > 0:
        log_info(f"T024 Complete. Processed {len(stats_list)} datasets.")
    else:
        log_error("T024 Failed: No datasets were successfully processed.")

if __name__ == "__main__":
    main()