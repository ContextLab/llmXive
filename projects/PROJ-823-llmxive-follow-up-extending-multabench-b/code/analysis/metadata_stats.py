"""
metadata_stats.py - Compute tabular feature statistics for MulTaBench datasets.

Computes cardinality, missingness, sparsity, and variance for tabular features
across ALL available datasets and outputs a summary CSV.
"""

import os
import sys
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from config import ensure_directories
from utils.logging import get_logger, log_info, log_warning, log_error, log_debug

logger = get_logger(__name__)

def load_dataset_list() -> List[Dict[str, Any]]:
    """
    Load the list of available datasets from the project configuration.
    Returns a list of dicts with 'dataset_id' and 'path' keys.
    """
    # Try to load from a standard dataset manifest or generate from data directory
    manifest_path = Path("data/datasets_manifest.json")
    data_dir = Path("data/raw")

    if manifest_path.exists():
        with open(manifest_path, 'r') as f:
            datasets = json.load(f)
        log_info(f"Loaded {len(datasets)} datasets from manifest {manifest_path}")
        return datasets

    # Fallback: scan data/raw directory for parquet/csv files
    if not data_dir.exists():
        log_warning(f"Data directory {data_dir} does not exist. Creating empty list.")
        return []

    datasets = []
    for ext in ['*.parquet', '*.csv', '*.json']:
        for file_path in data_dir.glob(ext):
            dataset_id = file_path.stem
            datasets.append({
                "dataset_id": dataset_id,
                "path": str(file_path)
            })
    
    log_info(f"Discovered {len(datasets)} datasets in {data_dir}")
    return datasets

def compute_feature_stats(df: pd.DataFrame) -> Dict[str, float]:
    """
    Compute cardinality, missingness, sparsity, and variance for numeric features.
    
    Args:
        df: Pandas DataFrame containing tabular features.
        
    Returns:
        Dictionary with aggregated statistics.
    """
    if df.empty:
        return {
            "cardinality": 0.0,
            "missingness": 0.0,
            "sparsity": 0.0,
            "variance": 0.0
        }

    # Select only numeric columns for variance and cardinality
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if not numeric_cols:
        # If no numeric columns, treat all as categorical or skip
        # For this implementation, we'll assume non-numeric columns have high cardinality
        # but 0 variance. We'll focus on what we can compute.
        log_debug("No numeric columns found. Computing stats for all columns where possible.")
        numeric_cols = df.columns.tolist()

    stats = {
        "cardinality": 0.0,
        "missingness": 0.0,
        "sparsity": 0.0,
        "variance": 0.0
    }

    total_rows = len(df)
    if total_rows == 0:
        return stats

    # Cardinality: Average number of unique values per feature
    unique_counts = []
    for col in numeric_cols:
        unique_counts.append(df[col].nunique())
    stats["cardinality"] = np.mean(unique_counts) if unique_counts else 0.0

    # Missingness: Average fraction of missing values per feature
    missing_counts = []
    for col in numeric_cols:
        missing_counts.append(df[col].isna().sum())
    stats["missingness"] = np.mean(missing_counts) / total_rows if missing_counts else 0.0

    # Sparsity: Average fraction of zero values (for numeric features)
    zero_counts = []
    for col in numeric_cols:
        zero_counts.append((df[col] == 0).sum())
    stats["sparsity"] = np.mean(zero_counts) / total_rows if zero_counts else 0.0

    # Variance: Average variance across numeric features
    variances = []
    for col in numeric_cols:
        # Drop NaNs before computing variance
        valid_values = df[col].dropna()
        if len(valid_values) > 1:
            variances.append(valid_values.var())
        else:
            variances.append(0.0)
    stats["variance"] = np.mean(variances) if variances else 0.0

    return stats

def process_single_dataset(dataset_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Process a single dataset and compute its tabular feature statistics.
    
    Args:
        dataset_info: Dictionary with 'dataset_id' and 'path'.
        
    Returns:
        Dictionary with dataset_id and computed stats, or None if processing fails.
    """
    dataset_id = dataset_info.get("dataset_id")
    file_path = dataset_info.get("path")

    if not file_path or not Path(file_path).exists():
        log_warning(f"Dataset file not found for {dataset_id}: {file_path}")
        return None

    try:
        log_info(f"Processing dataset {dataset_id} from {file_path}")
        
        # Load dataset
        if file_path.endswith('.parquet'):
            df = pd.read_parquet(file_path)
        elif file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith('.json'):
            df = pd.read_json(file_path)
        else:
            log_error(f"Unsupported file format for {dataset_id}: {file_path}")
            return None

        # Compute statistics
        stats = compute_feature_stats(df)
        
        result = {
            "dataset_id": dataset_id,
            "cardinality": round(stats["cardinality"], 4),
            "missingness": round(stats["missingness"], 4),
            "sparsity": round(stats["sparsity"], 4),
            "variance": round(stats["variance"], 4)
        }
        
        log_info(f"Completed processing {dataset_id}: {result}")
        return result

    except Exception as e:
        log_error(f"Failed to process dataset {dataset_id}: {str(e)}")
        return None

def save_summary_csv(results: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save the computed statistics to a CSV file.
    
    Args:
        results: List of dictionaries with dataset statistics.
        output_path: Path to the output CSV file.
    """
    if not results:
        log_warning("No results to save. Creating empty CSV with headers.")
        df_empty = pd.DataFrame(columns=["dataset_id", "cardinality", "missingness", "sparsity", "variance"])
        df_empty.to_csv(output_path, index=False)
        return

    df = pd.DataFrame(results)
    
    # Ensure column order
    columns = ["dataset_id", "cardinality", "missingness", "sparsity", "variance"]
    df = df[columns]
    
    df.to_csv(output_path, index=False)
    log_info(f"Saved summary statistics to {output_path} ({len(results)} datasets)")

def main() -> None:
    """
    Main entry point for computing metadata statistics across all datasets.
    """
    log_info("Starting metadata statistics computation for all datasets")
    
    # Ensure output directories exist
    ensure_directories()
    
    # Load dataset list
    datasets = load_dataset_list()
    if not datasets:
        log_warning("No datasets found. Exiting.")
        return

    # Process each dataset
    results = []
    for dataset_info in datasets:
        result = process_single_dataset(dataset_info)
        if result:
            results.append(result)
    
    # Generate output path
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"data/processed/metadata_stats_summary.csv"
    
    # Save results
    save_summary_csv(results, output_path)
    
    log_info(f"Metadata statistics computation completed. Output: {output_path}")

if __name__ == "__main__":
    main()
