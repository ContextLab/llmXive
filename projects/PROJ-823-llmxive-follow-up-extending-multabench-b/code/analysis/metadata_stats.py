"""
Metadata Statistics Computation Module.

Computes cardinality, missingness, sparsity, and variance for tabular features
across all available datasets in the MulTaBench repository.
"""
import os
import sys
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.logging import get_logger, log_info, log_warning, log_error, log_debug

logger = get_logger(__name__)

# Constants
DATA_RAW_DIR = project_root / "data" / "raw"
DATA_PROCESSED_DIR = project_root / "data" / "processed"

# Ensure output directory exists
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def load_dataset_list() -> List[str]:
    """
    Load the list of available dataset IDs from the raw data directory.
    
    Returns:
        List of dataset IDs (directory names or file stems) found in data/raw/
    """
    if not DATA_RAW_DIR.exists():
        log_error(f"Raw data directory not found: {DATA_RAW_DIR}")
        return []
    
    datasets = []
    for item in DATA_RAW_DIR.iterdir():
        if item.is_dir():
            datasets.append(item.name)
        elif item.is_file() and item.suffix == '.csv':
            # Assume file stem is dataset ID
            datasets.append(item.stem)
    
    log_info(f"Found {len(datasets)} datasets in {DATA_RAW_DIR}")
    return sorted(datasets)

def compute_feature_stats(df: pd.DataFrame, numeric_cols: List[str]) -> Dict[str, Dict[str, float]]:
    """
    Compute statistical features for numeric columns.
    
    Args:
        df: DataFrame containing tabular data
        numeric_cols: List of column names to analyze
        
    Returns:
        Dictionary mapping column name to stats dict
    """
    stats = {}
    for col in numeric_cols:
        if col not in df.columns:
            continue
        
        series = df[col]
        count = series.count()
        total = len(series)
        
        # Missingness: proportion of NaN values
        missingness = (total - count) / total if total > 0 else 0.0
        
        # Sparsity: proportion of zero values among non-missing
        non_missing = series.dropna()
        if len(non_missing) > 0:
            zero_count = (non_missing == 0).sum()
            sparsity = zero_count / len(non_missing)
        else:
            sparsity = 0.0
        
        # Variance: population variance (ddof=0) or sample variance (ddof=1)
        # Using ddof=1 (sample variance) is standard for statistics
        if len(non_missing) > 1:
            variance = non_missing.var(ddof=1)
        else:
            variance = 0.0
        
        stats[col] = {
            'missingness': float(missingness),
            'sparsity': float(sparsity),
            'variance': float(variance),
            'count': int(count),
            'total': int(total)
        }
    
    return stats

def compute_cardinality_for_dataset(dataset_id: str, df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute cardinality for categorical and numeric features.
    
    For this implementation, we treat all non-numeric columns as categorical
    and compute their unique value counts. For numeric columns, we compute
    the number of unique values.
    
    Args:
        dataset_id: Identifier for the dataset
        df: DataFrame containing tabular data
        
    Returns:
        Dictionary with dataset_id and cardinality metric
    """
    # Select only object/string columns for cardinality (categorical)
    # Or compute unique values for all columns if needed
    cardinalities = {}
    
    for col in df.columns:
        if df[col].dtype == 'object' or df[col].dtype.name.startswith('string'):
            # Categorical: count unique values
            unique_count = df[col].nunique()
            cardinalities[col] = unique_count
        elif pd.api.types.is_numeric_dtype(df[col]):
            # Numeric: count unique values (discrete approximation)
            unique_count = df[col].nunique()
            cardinalities[col] = unique_count
    
    if not cardinalities:
        log_warning(f"No cardinality data found for dataset {dataset_id}")
        return {'dataset_id': dataset_id, 'cardinality': 0.0}
    
    # Mean cardinality across all features
    mean_cardinality = np.mean(list(cardinalities.values()))
    
    return {
        'dataset_id': dataset_id,
        'cardinality': float(mean_cardinality)
    }

def compute_missingness_for_dataset(dataset_id: str, df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute mean missingness rate across all tabular features.
    
    Args:
        dataset_id: Identifier for the dataset
        df: DataFrame containing tabular data
        
    Returns:
        Dictionary with dataset_id and mean missingness rate
    """
    stats = compute_feature_stats(df, list(df.columns))
    
    if not stats:
        log_warning(f"No missingness data found for dataset {dataset_id}")
        return {'dataset_id': dataset_id, 'missingness': 0.0}
    
    missingness_values = [s['missingness'] for s in stats.values()]
    mean_missingness = np.mean(missingness_values)
    
    return {
        'dataset_id': dataset_id,
        'missingness': float(mean_missingness)
    }

def compute_sparsity_for_dataset(dataset_id: str, df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute mean sparsity rate across all tabular features.
    
    Args:
        dataset_id: Identifier for the dataset
        df: DataFrame containing tabular data
        
    Returns:
        Dictionary with dataset_id and mean sparsity rate
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if not numeric_cols:
        log_warning(f"No numeric columns found for sparsity calculation in dataset {dataset_id}")
        return {'dataset_id': dataset_id, 'sparsity': 0.0}
    
    stats = compute_feature_stats(df, numeric_cols)
    
    if not stats:
        return {'dataset_id': dataset_id, 'sparsity': 0.0}
    
    sparsity_values = [s['sparsity'] for s in stats.values()]
    mean_sparsity = np.mean(sparsity_values)
    
    return {
        'dataset_id': dataset_id,
        'sparsity': float(mean_sparsity)
    }

def compute_variance_for_dataset(dataset_id: str, df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute mean variance across all numeric tabular features for a dataset.
    
    This function calculates the sample variance (ddof=1) for each numeric feature
    and returns the mean variance across all features.
    
    Args:
        dataset_id: Identifier for the dataset
        df: DataFrame containing tabular data
        
    Returns:
        Dictionary with dataset_id and mean variance
    """
    # Select only numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if not numeric_cols:
        log_warning(f"No numeric columns found for variance calculation in dataset {dataset_id}")
        return {'dataset_id': dataset_id, 'variance': 0.0}
    
    stats = compute_feature_stats(df, numeric_cols)
    
    if not stats:
        return {'dataset_id': dataset_id, 'variance': 0.0}
    
    variance_values = [s['variance'] for s in stats.values()]
    
    # Filter out infinite or NaN values
    variance_values = [v for v in variance_values if not np.isnan(v) and not np.isinf(v)]
    
    if not variance_values:
        log_warning(f"All variances are NaN/Inf for dataset {dataset_id}")
        return {'dataset_id': dataset_id, 'variance': 0.0}
    
    mean_variance = np.mean(variance_values)
    
    return {
        'dataset_id': dataset_id,
        'variance': float(mean_variance)
    }

def process_single_dataset(dataset_id: str) -> Optional[Dict[str, Any]]:
    """
    Process a single dataset to compute all metadata statistics.
    
    Args:
        dataset_id: Identifier for the dataset
        
    Returns:
        Dictionary containing all computed statistics or None if processing fails
    """
    log_info(f"Processing dataset: {dataset_id}")
    
    dataset_path = DATA_RAW_DIR / dataset_id
    
    # Check if it's a directory or a file
    if dataset_path.is_dir():
        # Look for CSV files in the directory
        csv_files = list(dataset_path.glob("*.csv"))
        if not csv_files:
            log_error(f"No CSV files found in directory: {dataset_path}")
            return None
        # Use the first CSV file
        data_file = csv_files[0]
    elif dataset_path.is_file() and dataset_path.suffix == '.csv':
        data_file = dataset_path
    else:
        # Try to find a CSV with the dataset_id as stem
        csv_file = DATA_RAW_DIR / f"{dataset_id}.csv"
        if csv_file.exists():
            data_file = csv_file
        else:
            log_error(f"Could not locate data for dataset: {dataset_id}")
            return None
    
    try:
        df = pd.read_csv(data_file)
        log_debug(f"Loaded {len(df)} rows and {len(df.columns)} columns from {data_file}")
    except Exception as e:
        log_error(f"Failed to load {data_file}: {e}")
        return None
    
    # Compute statistics
    results = {
        'dataset_id': dataset_id,
        'cardinality': compute_cardinality_for_dataset(dataset_id, df)['cardinality'],
        'missingness': compute_missingness_for_dataset(dataset_id, df)['missingness'],
        'sparsity': compute_sparsity_for_dataset(dataset_id, df)['sparsity'],
        'variance': compute_variance_for_dataset(dataset_id, df)['variance']
    }
    
    log_info(f"Completed processing dataset: {dataset_id}")
    return results

def save_summary_csv(results: List[Dict[str, Any]], output_path: Path, metric_name: str) -> None:
    """
    Save computed statistics to a CSV file.
    
    Args:
        results: List of dictionaries containing statistics
        output_path: Path to the output CSV file
        metric_name: Name of the metric column
    """
    if not results:
        log_warning("No results to save")
        return
    
    df_out = pd.DataFrame(results)
    df_out = df_out.sort_values('dataset_id')
    
    # Ensure column order
    cols = ['dataset_id', metric_name]
    df_out = df_out[cols]
    
    df_out.to_csv(output_path, index=False)
    log_info(f"Saved {len(results)} records to {output_path}")

def main():
    """
    Main entry point for computing variance statistics for all datasets.
    """
    log_info("Starting variance computation for all datasets")
    
    dataset_ids = load_dataset_list()
    
    if not dataset_ids:
        log_error("No datasets found to process")
        sys.exit(1)
    
    all_results = []
    
    for dataset_id in dataset_ids:
        result = process_single_dataset(dataset_id)
        if result:
            all_results.append(result)
    
    if not all_results:
        log_error("No results computed from any dataset")
        sys.exit(1)
    
    # Save variance summary
    output_path = DATA_PROCESSED_DIR / "metadata_stats_variance.csv"
    save_summary_csv(all_results, output_path, 'variance')
    
    log_info("Variance computation completed successfully")
    return all_results

if __name__ == "__main__":
    main()
