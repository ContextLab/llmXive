import os
import sys
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np

from config import ensure_directories
from utils.logging import get_logger, log_info, log_error, log_warning

logger = get_logger(__name__)

# Constants
RAW_DATA_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
DATASET_LIST_FILE = Path("data/raw/dataset_list.json")

def load_dataset_list() -> List[str]:
    """Load the list of available dataset IDs."""
    if not DATASET_LIST_FILE.exists():
        log_error(f"Dataset list file not found: {DATASET_LIST_FILE}")
        return []
    
    try:
        with open(DATASET_LIST_FILE, 'r') as f:
            data = json.load(f)
            return data.get("datasets", [])
    except Exception as e:
        log_error(f"Error loading dataset list: {e}")
        return []

def load_raw_tabular_data(dataset_id: str) -> Optional[pd.DataFrame]:
    """Load raw tabular data for a specific dataset."""
    csv_path = RAW_DATA_DIR / f"{dataset_id}.csv"
    
    if not csv_path.exists():
        log_warning(f"Raw tabular data not found for dataset {dataset_id}: {csv_path}")
        return None
    
    try:
        df = pd.read_csv(csv_path)
        log_info(f"Loaded tabular data for {dataset_id}: shape {df.shape}")
        return df
    except Exception as e:
        log_error(f"Error loading tabular data for {dataset_id}: {e}")
        return None

def compute_cardinality_for_dataset(df: pd.DataFrame) -> Dict[str, float]:
    """Compute cardinality for each categorical feature in the dataset."""
    cardinalities = {}
    for col in df.columns:
        if df[col].dtype == 'object' or df[col].dtype.name == 'category':
            cardinalities[col] = float(df[col].nunique())
        else:
            # For numeric, treat as continuous (effectively infinite cardinality for this metric)
            # or count unique values if low cardinality
            unique_count = df[col].nunique()
            if unique_count < 20:
                cardinalities[col] = float(unique_count)
            else:
                cardinalities[col] = -1.0  # Marker for high cardinality/continuous
    
    return cardinalities

def compute_missingness_for_dataset(df: pd.DataFrame) -> Dict[str, float]:
    """Compute missingness rate for each feature."""
    missingness = {}
    for col in df.columns:
        total = len(df)
        missing = df[col].isna().sum()
        missingness[col] = float(missing / total) if total > 0 else 0.0
    return missingness

def compute_sparsity_for_dataset(df: pd.DataFrame) -> Dict[str, float]:
    """Compute sparsity (proportion of zeros) for numeric features."""
    sparsity = {}
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            total = len(df)
            zeros = (df[col] == 0).sum()
            sparsity[col] = float(zeros / total) if total > 0 else 0.0
        else:
            sparsity[col] = 0.0  # Non-numeric columns are not sparse in this context
    return sparsity

def compute_variance_for_dataset(df: pd.DataFrame) -> Dict[str, float]:
    """
    Compute variance for each numeric feature in the dataset.
    Returns a dictionary mapping feature name to variance.
    Non-numeric features are skipped.
    """
    variance = {}
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            # Drop NaNs for variance calculation
            clean_series = df[col].dropna()
            if len(clean_series) > 1:
                var_val = clean_series.var()
                variance[col] = float(var_val)
            else:
                variance[col] = 0.0
        else:
            variance[col] = 0.0  # Non-numeric features have no variance in this context
    return variance

def compute_feature_stats(df: pd.DataFrame) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, float], Dict[str, float]]:
    """
    Compute all metadata stats for a single dataset.
    Returns: (cardinality, missingness, sparsity, variance)
    """
    cardinality = compute_cardinality_for_dataset(df)
    missingness = compute_missingness_for_dataset(df)
    sparsity = compute_sparsity_for_dataset(df)
    variance = compute_variance_for_dataset(df)
    return cardinality, missingness, sparsity, variance

def process_single_dataset(dataset_id: str) -> Optional[Dict[str, Any]]:
    """Process a single dataset and return its stats."""
    log_info(f"Processing dataset: {dataset_id}")
    df = load_raw_tabular_data(dataset_id)
    
    if df is None:
        log_error(f"Skipping {dataset_id} due to missing data")
        return None
    
    try:
        cardinality, missingness, sparsity, variance = compute_feature_stats(df)
        
        # Calculate mean variance across all numeric features for this dataset
        numeric_variances = [v for k, v in variance.items() if k in df.columns and pd.api.types.is_numeric_dtype(df[k])]
        mean_variance = np.mean(numeric_variances) if numeric_variances else 0.0
        
        return {
            "dataset_id": dataset_id,
            "cardinality": cardinality,
            "missingness": missingness,
            "sparsity": sparsity,
            "variance": variance,
            "mean_variance": mean_variance
        }
    except Exception as e:
        log_error(f"Error processing {dataset_id}: {e}")
        return None

def save_summary_csv(results: List[Dict[str, Any]], output_path: Path, stat_type: str):
    """Save a summary CSV for a specific stat type."""
    if not results:
        log_warning("No results to save")
        return
    
    data_rows = []
    for res in results:
        dataset_id = res["dataset_id"]
        if stat_type == "variance":
            val = res.get("mean_variance", 0.0)
        else:
            # For other types, we might aggregate differently, but T024d is specifically variance
            val = 0.0 
        
        data_rows.append({"dataset_id": dataset_id, stat_type: val})
    
    df_out = pd.DataFrame(data_rows)
    df_out.to_csv(output_path, index=False)
    log_info(f"Saved {stat_type} summary to {output_path}")

def main():
    """Main entry point for computing metadata statistics."""
    ensure_directories()
    
    log_info("Starting metadata statistics computation (Variance)")
    
    dataset_ids = load_dataset_list()
    if not dataset_ids:
        log_error("No datasets found to process")
        sys.exit(1)
    
    log_info(f"Found {len(dataset_ids)} datasets to process")
    
    all_results = []
    for ds_id in dataset_ids:
        result = process_single_dataset(ds_id)
        if result:
            all_results.append(result)
    
    if not all_results:
        log_error("No datasets were successfully processed")
        sys.exit(1)
    
    # Save the variance summary CSV
    output_path = PROCESSED_DIR / "metadata_stats_variance.csv"
    save_summary_csv(all_results, output_path, "variance")
    
    log_info("Variance computation complete")

if __name__ == "__main__":
    main()
