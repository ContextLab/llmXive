import os
import sys
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np

# Import logging utilities if available, otherwise fallback to standard logging
try:
    from utils.logging import get_logger, log_info, log_error, log_warning
    logger = get_logger(__name__)
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

# Constants
RAW_DATA_DIR = Path("data/raw")
PROCESSED_DATA_DIR = Path("data/processed")
SUMMARY_CSV_PATH = PROCESSED_DATA_DIR / "metadata_stats_summary.csv"

def load_dataset_list() -> List[Dict[str, Any]]:
    """
    Scans data/raw/ for available datasets and returns a list of dataset metadata.
    Expects datasets to be in subdirectories or as specific file patterns.
    For this implementation, we assume tabular data is in CSV files within data/raw/.
    """
    datasets = []
    if not RAW_DATA_DIR.exists():
        logger.warning(f"Raw data directory {RAW_DATA_DIR} does not exist.")
        return datasets

    # Look for CSV files in data/raw/
    for file_path in RAW_DATA_DIR.glob("*.csv"):
        # Skip the baselines file if present, as it's metadata, not a dataset
        if "baselines" in file_path.name.lower():
            continue
        
        dataset_id = file_path.stem
        datasets.append({
            "dataset_id": dataset_id,
            "file_path": str(file_path)
        })
    
    # Also check for subdirectories that might contain datasets
    for item in RAW_DATA_DIR.iterdir():
        if item.is_dir():
            # Assume the directory name is the dataset_id
            # Look for a CSV inside
            csv_files = list(item.glob("*.csv"))
            if csv_files:
                datasets.append({
                    "dataset_id": item.name,
                    "file_path": str(csv_files[0]) # Take the first CSV found
                })
    
    return datasets

def load_raw_tabular_data(file_path: str) -> pd.DataFrame:
    """
    Loads a tabular dataset from a CSV file.
    """
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        logger.error(f"Failed to load dataset from {file_path}: {e}")
        raise

def compute_cardinality(df: pd.DataFrame) -> float:
    """
    Computes the average cardinality of categorical features.
    For numerical features, returns 0 or a placeholder if not applicable.
    Here we calculate the number of unique values across all non-numeric columns
    and average them, or return 0 if no categorical columns exist.
    """
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns
    if len(categorical_cols) == 0:
        return 0.0
    
    cardinalities = [df[col].nunique() for col in categorical_cols]
    return float(np.mean(cardinalities))

def compute_missingness(df: pd.DataFrame) -> float:
    """
    Computes the fraction of missing values in the dataset.
    """
    total_cells = df.size
    if total_cells == 0:
        return 0.0
    missing_count = df.isnull().sum().sum()
    return float(missing_count / total_cells)

def compute_sparsity(df: pd.DataFrame) -> float:
    """
    Computes the sparsity of the dataset (fraction of zero values).
    Only considers numerical columns.
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) == 0:
        return 0.0
    
    numeric_df = df[numeric_cols]
    total_zeros = (numeric_df == 0).sum().sum()
    total_cells = numeric_df.size
    
    if total_cells == 0:
        return 0.0
    return float(total_zeros / total_cells)

def compute_variance(df: pd.DataFrame) -> float:
    """
    Computes the average variance of numerical features.
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) == 0:
        return 0.0
    
    variances = df[numeric_cols].var(numeric_only=True).dropna()
    if len(variances) == 0:
        return 0.0
    
    return float(np.mean(variances))

def compute_feature_stats(df: pd.DataFrame) -> Dict[str, float]:
    """
    Computes all metadata stats for a single dataset.
    """
    return {
        "cardinality": compute_cardinality(df),
        "missingness": compute_missingness(df),
        "sparsity": compute_sparsity(df),
        "variance": compute_variance(df)
    }

def process_single_dataset(dataset_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Processes a single dataset and returns its stats.
    """
    try:
        df = load_raw_tabular_data(dataset_info["file_path"])
        stats = compute_feature_stats(df)
        stats["dataset_id"] = dataset_info["dataset_id"]
        return stats
    except Exception as e:
        logger.error(f"Error processing dataset {dataset_info['dataset_id']}: {e}")
        return None

def save_summary_csv(stats_list: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Aggregates stats into a single CSV file.
    """
    if not stats_list:
        logger.warning("No stats to save.")
        return

    df_stats = pd.DataFrame(stats_list)
    # Ensure columns are in the specified order
    expected_columns = ["dataset_id", "cardinality", "missingness", "sparsity", "variance"]
    # Reindex to ensure order, adding missing columns with NaN if necessary (though logic above should prevent this)
    if not all(col in df_stats.columns for col in expected_columns):
        # This case should ideally not happen if compute_feature_stats always returns these keys
        for col in expected_columns:
            if col not in df_stats.columns:
                df_stats[col] = np.nan
    
    df_stats = df_stats[expected_columns]
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df_stats.to_csv(output_path, index=False)
    logger.info(f"Saved metadata stats summary to {output_path}")

def compute_all_stats() -> List[Dict[str, Any]]:
    """
    Iterates through all datasets and computes stats for each.
    """
    datasets = load_dataset_list()
    if not datasets:
        logger.warning("No datasets found in data/raw/")
        return []
    
    logger.info(f"Found {len(datasets)} datasets to process.")
    stats_list = []
    
    for ds in datasets:
        logger.info(f"Processing dataset: {ds['dataset_id']}")
        result = process_single_dataset(ds)
        if result:
            stats_list.append(result)
    
    return stats_list

def aggregate_stats() -> None:
    """
    Main entry point for T024c: Aggregates stats from T024b logic into a single CSV.
    This function orchestrates loading datasets, computing stats, and saving the summary.
    """
    logger.info("Starting metadata stats aggregation (T024c)...")
    
    # 1. Compute stats for all datasets
    stats_list = compute_all_stats()
    
    # 2. Save to CSV
    if stats_list:
        save_summary_csv(stats_list, SUMMARY_CSV_PATH)
        logger.info("Aggregation complete.")
    else:
        logger.error("No stats were generated. CSV not created.")
        # We do not raise an exception here to allow the pipeline to continue 
        # if the lack of data is a valid state (e.g., empty raw dir), 
        # but the task requirement is to produce the file if possible.

def main():
    """
    CLI entry point for metadata stats aggregation.
    """
    logger.info("Running metadata_stats.py main...")
    aggregate_stats()

if __name__ == "__main__":
    main()