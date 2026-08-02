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
    """
    raw_path = Path("data/raw")
    if not raw_path.exists():
        log_error("data/raw/ does not exist.")
        return []
    
    # Assume datasets are in subdirectories or files with specific naming
    # For MulTaBench, we might have a list of CSVs or folders
    # We will look for CSV files
    datasets = []
    for item in raw_path.iterdir():
        if item.is_file() and item.suffix == '.csv':
            datasets.append(item.stem)
        elif item.is_dir():
            datasets.append(item.name)
    
    return datasets

def compute_feature_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes cardinality, missingness, sparsity, and variance for numeric features.
    """
    stats = {}
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Remove 'dataset_id' if present
    if 'dataset_id' in numeric_cols:
        numeric_cols.remove('dataset_id')
    
    cardinality = {}
    missingness = {}
    sparsity = {}
    variance = {}
    
    for col in numeric_cols:
        col_data = df[col]
        
        # Cardinality (unique values)
        cardinality[col] = col_data.nunique()
        
        # Missingness (percentage)
        missingness[col] = col_data.isna().sum() / len(col_data)
        
        # Sparsity (percentage of zeros)
        sparsity[col] = (col_data == 0).sum() / len(col_data)
        
        # Variance
        variance[col] = col_data.var()
    
    return {
        "cardinality": cardinality,
        "missingness": missingness,
        "sparsity": sparsity,
        "variance": variance
    }

def process_single_dataset(dataset_id: str) -> Dict[str, Any]:
    """
    Loads a single dataset and computes its stats.
    """
    raw_path = Path("data/raw") / f"{dataset_id}.csv"
    if not raw_path.exists():
        # Try without extension or in subdirectory
        raw_path = Path("data/raw") / dataset_id
    
    try:
        if raw_path.is_dir():
            # Load all CSVs in the directory
            dfs = []
            for f in raw_path.glob("*.csv"):
                dfs.append(pd.read_csv(f))
            if dfs:
                df = pd.concat(dfs, ignore_index=True)
            else:
                raise FileNotFoundError(f"No CSV files found in {raw_path}")
        else:
            df = pd.read_csv(raw_path)
        
        stats = compute_feature_stats(df)
        stats["dataset_id"] = dataset_id
        return stats
    except Exception as e:
        log_error(f"Failed to process dataset {dataset_id}: {e}")
        return None

def save_summary_csv(stats_list: List[Dict[str, Any]], output_path: Path):
    """
    Saves the summary stats to a CSV file.
    """
    # Flatten the stats
    rows = []
    for s in stats_list:
        if s is None:
            continue
        row = {
            "dataset_id": s.get("dataset_id"),
            "cardinality": np.mean(list(s.get("cardinality", {}).values())) if s.get("cardinality") else 0,
            "missingness": np.mean(list(s.get("missingness", {}).values())) if s.get("missingness") else 0,
            "sparsity": np.mean(list(s.get("sparsity", {}).values())) if s.get("sparsity") else 0,
            "variance": np.mean(list(s.get("variance", {}).values())) if s.get("variance") else 0
        }
        rows.append(row)
    
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    log_info(f"Saved summary to {output_path}")

def main():
    """
    Main entry point for T024.
    """
    ensure_dirs = True # Already done in other tasks
    dataset_list = load_dataset_list()
    
    if not dataset_list:
        log_error("No datasets found.")
        return
    
    stats_list = []
    for ds_id in dataset_list:
        stats = process_single_dataset(ds_id)
        if stats:
            stats_list.append(stats)
    
    output_path = Path("data/processed/metadata_stats_summary.csv")
    save_summary_csv(stats_list, output_path)

if __name__ == "__main__":
    main()
