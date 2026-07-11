"""
Compute tabular feature metadata statistics for all available datasets.

Outputs a single summary CSV: data/processed/metadata_stats_summary.csv
Columns: dataset_id, cardinality, missingness, sparsity, variance
"""
import os
import sys
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import pandas as pd
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from utils.logging import get_logger, log_info, log_warning, log_error, log_debug
from config import DATA_DIR, PROCESSED_DIR

logger = get_logger(__name__)

def compute_feature_stats(df: pd.DataFrame, dataset_id: str) -> Dict[str, Any]:
    """
    Compute cardinality, missingness, sparsity, and variance for all numeric features.
    
    Args:
        df: DataFrame containing tabular features
        dataset_id: Identifier for the dataset
    
    Returns:
        Dictionary with aggregated statistics
    """
    if df.empty:
        log_warning(f"Dataset {dataset_id} is empty. Skipping statistics computation.")
        return {
            "dataset_id": dataset_id,
            "cardinality": 0.0,
            "missingness": 0.0,
            "sparsity": 0.0,
            "variance": 0.0
        }

    # Select only numeric columns for variance and cardinality calculations
    numeric_df = df.select_dtypes(include=[np.number])
    
    if numeric_df.empty:
        log_warning(f"Dataset {dataset_id} has no numeric features.")
        return {
            "dataset_id": dataset_id,
            "cardinality": 0.0,
            "missingness": 0.0,
            "sparsity": 0.0,
            "variance": 0.0
        }

    # Calculate missingness: fraction of missing values across all numeric features
    total_cells = numeric_df.size
    missing_cells = numeric_df.isna().sum().sum()
    missingness = missing_cells / total_cells if total_cells > 0 else 0.0

    # Calculate sparsity: fraction of zero values across all numeric features
    zero_cells = (numeric_df == 0).sum().sum()
    sparsity = zero_cells / total_cells if total_cells > 0 else 0.0

    # Calculate variance: average variance across all numeric features
    # Only compute for features with >1 unique value to avoid division by zero
    variances = []
    for col in numeric_df.columns:
        col_data = numeric_df[col].dropna()
        if len(col_data) > 1:
            var = col_data.var()
            if not np.isnan(var):
                variances.append(var)
    
    avg_variance = np.mean(variances) if variances else 0.0

    # Calculate cardinality: average number of unique values per feature
    cardinalities = []
    for col in numeric_df.columns:
        col_data = numeric_df[col].dropna()
        if len(col_data) > 0:
            unique_count = col_data.nunique()
            cardinalities.append(unique_count)
    
    avg_cardinality = np.mean(cardinalities) if cardinalities else 0.0

    return {
        "dataset_id": dataset_id,
        "cardinality": avg_cardinality,
        "missingness": missingness,
        "sparsity": sparsity,
        "variance": avg_variance
    }

def load_dataset_list() -> List[Dict[str, Any]]:
    """
    Load the list of available datasets from the project's data configuration.
    Returns a list of dataset metadata dictionaries.
    """
    datasets_dir = DATA_DIR / "datasets"
    if not datasets_dir.exists():
        log_error(f"Datasets directory not found: {datasets_dir}")
        return []
    
    dataset_list = []
    for item in datasets_dir.iterdir():
        if item.is_dir():
            dataset_id = item.name
            # Check for tabular data files
            tabular_files = list(item.glob("*.csv")) + list(item.glob("*.parquet"))
            if tabular_files:
                dataset_list.append({
                    "dataset_id": dataset_id,
                    "path": str(item),
                    "tabular_files": [str(f) for f in tabular_files]
                })
    
    log_info(f"Found {len(dataset_list)} datasets with tabular data.")
    return dataset_list

def process_single_dataset(dataset_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Process a single dataset and compute its metadata statistics.
    
    Args:
        dataset_info: Dictionary containing dataset path and metadata
    
    Returns:
        Dictionary with computed statistics or None if processing fails
    """
    dataset_id = dataset_info["dataset_id"]
    tabular_files = dataset_info["tabular_files"]
    
    log_info(f"Processing dataset: {dataset_id}")
    
    try:
        # Load the first available tabular file
        df = None
        for file_path in tabular_files:
            try:
                if file_path.endswith('.parquet'):
                    df = pd.read_parquet(file_path)
                elif file_path.endswith('.csv'):
                    df = pd.read_csv(file_path)
                else:
                    continue
                
                if df is not None and not df.empty:
                    log_debug(f"Loaded {len(df)} rows from {file_path}")
                    break
            except Exception as e:
                log_warning(f"Failed to load {file_path}: {e}")
                continue
        
        if df is None or df.empty:
            log_warning(f"No valid data loaded for dataset {dataset_id}")
            return compute_feature_stats(pd.DataFrame(), dataset_id)
        
        # Compute statistics
        stats = compute_feature_stats(df, dataset_id)
        log_info(f"Completed statistics for {dataset_id}: "
                 f"cardinality={stats['cardinality']:.2f}, "
                 f"missingness={stats['missingness']:.4f}, "
                 f"sparsity={stats['sparsity']:.4f}, "
                 f"variance={stats['variance']:.4f}")
        
        return stats
        
    except Exception as e:
        log_error(f"Failed to process dataset {dataset_id}: {e}")
        return None

def save_summary_csv(stats_list: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save the computed statistics to a CSV file.
    
    Args:
        stats_list: List of statistics dictionaries
        output_path: Path to the output CSV file
    """
    if not stats_list:
        log_warning("No statistics to save.")
        return
    
    df_stats = pd.DataFrame(stats_list)
    
    # Ensure correct column order
    columns = ["dataset_id", "cardinality", "missingness", "sparsity", "variance"]
    df_stats = df_stats[columns]
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df_stats.to_csv(output_path, index=False)
    log_info(f"Saved metadata statistics summary to {output_path}")

def main():
    """
    Main entry point for computing metadata statistics across all datasets.
    """
    log_info("Starting metadata statistics computation for all datasets...")
    
    # Load dataset list
    datasets = load_dataset_list()
    if not datasets:
        log_error("No datasets found to process.")
        sys.exit(1)
    
    # Process each dataset
    all_stats = []
    for dataset_info in datasets:
        stats = process_single_dataset(dataset_info)
        if stats is not None:
            all_stats.append(stats)
    
    if not all_stats:
        log_error("No statistics computed successfully.")
        sys.exit(1)
    
    # Define output path
    output_path = PROCESSED_DIR / "metadata_stats_summary.csv"
    
    # Save results
    save_summary_csv(all_stats, output_path)
    
    log_info("Metadata statistics computation completed successfully.")

if __name__ == "__main__":
    main()
