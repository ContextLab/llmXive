import os
import sys
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

# Ensure the parent directory is in the path for imports if running as script
# but rely on project structure for standard execution
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

def get_logger():
    """Simple logger for the module."""
    import logging
    return logging.getLogger(__name__)

def load_dataset_list() -> List[str]:
    """
    Loads the list of available dataset IDs from the raw data directory.
    Assumes datasets are named with a specific pattern or listed in a manifest.
    For this implementation, we scan the data/raw directory for CSV/Parquet files
    that represent datasets, or look for a specific manifest if it exists.
    Given the context of MulTaBench, we assume a list of dataset IDs is available
    or can be inferred from the filenames in data/raw/.
    """
    datasets = []
    if not DATA_RAW_DIR.exists():
        get_logger().warning(f"Raw data directory {DATA_RAW_DIR} does not exist.")
        return datasets

    # Heuristic: Look for files that look like dataset files
    # MulTaBench usually has files like 'dataset_name.csv' or 'dataset_name.parquet'
    # We will assume the filename stem (without extension) is the dataset_id
    # unless there is a specific manifest.
    for ext in ['*.csv', '*.parquet', '*.csv.gz']:
        for f in DATA_RAW_DIR.glob(ext):
            dataset_id = f.stem
            # Filter out obvious non-dataset files if necessary
            if not dataset_id.startswith('.'):
                datasets.append(dataset_id)
    
    # If no files found, check for a manifest
    if not datasets:
        manifest_path = DATA_RAW_DIR / "dataset_manifest.json"
        if manifest_path.exists():
            with open(manifest_path, 'r') as f:
                data = json.load(f)
                datasets = data.get('datasets', [])
    
    return sorted(list(set(datasets)))

def load_raw_tabular_data(dataset_id: str) -> Optional[pd.DataFrame]:
    """
    Loads the raw tabular data for a specific dataset.
    Tries common file extensions in data/raw/.
    """
    possible_paths = [
        DATA_RAW_DIR / f"{dataset_id}.csv",
        DATA_RAW_DIR / f"{dataset_id}.parquet",
        DATA_RAW_DIR / f"{dataset_id}.csv.gz"
    ]
    
    for path in possible_paths:
        if path.exists():
            if path.suffix == '.parquet':
                return pd.read_parquet(path)
            else:
                return pd.read_csv(path)
    
    get_logger().error(f"Could not find raw data for dataset: {dataset_id}")
    return None

def compute_cardinality_for_dataset(df: pd.DataFrame) -> float:
    """
    Computes the average cardinality (number of unique values) across all features.
    """
    if df.empty:
        return 0.0
    
    cardinalities = []
    for col in df.columns:
        # Only compute for non-numeric or numeric columns as appropriate
        # Cardinality is meaningful for categorical or discrete numeric
        try:
            unique_count = df[col].nunique()
            cardinalities.append(unique_count)
        except Exception:
            continue
    
    if not cardinalities:
        return 0.0
    
    return float(np.mean(cardinalities))

def compute_missingness_for_dataset(df: pd.DataFrame) -> float:
    """
    Computes the average missingness rate across all features.
    """
    if df.empty:
        return 0.0
    
    missing_counts = []
    for col in df.columns:
        missing_count = df[col].isna().sum()
        missing_counts.append(missing_count / len(df))
    
    if not missing_counts:
        return 0.0
    
    return float(np.mean(missing_counts))

def compute_sparsity_for_dataset(df: pd.DataFrame) -> float:
    """
    Computes the average sparsity (proportion of zero values) across all features.
    Only applicable to numeric columns.
    """
    if df.empty:
        return 0.0
    
    sparsities = []
    for col in df.select_dtypes(include=[np.number]).columns:
        total = len(df)
        if total == 0:
            continue
        zero_count = (df[col] == 0).sum()
        sparsities.append(zero_count / total)
    
    if not sparsities:
        return 0.0
    
    return float(np.mean(sparsities))

def compute_variance_for_dataset(df: pd.DataFrame) -> float:
    """
    Computes the mean variance across all numeric tabular features for a dataset.
    
    Returns:
        float: The mean variance of all numeric columns. Returns 0.0 if no numeric columns.
    """
    if df.empty:
        return 0.0
    
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.empty:
        return 0.0
    
    variances = []
    for col in numeric_df.columns:
        # Calculate variance (ddof=1 for sample variance, standard in stats)
        # If a column is constant, variance is 0.
        var = numeric_df[col].var()
        if not pd.isna(var):
            variances.append(var)
    
    if not variances:
        return 0.0
    
    return float(np.mean(variances))

def compute_feature_stats(df: pd.DataFrame) -> Dict[str, float]:
    """
    Computes all metadata stats for a single dataframe.
    """
    return {
        'cardinality': compute_cardinality_for_dataset(df),
        'missingness': compute_missingness_for_dataset(df),
        'sparsity': compute_sparsity_for_dataset(df),
        'variance': compute_variance_for_dataset(df)
    }

def process_single_dataset(dataset_id: str) -> Optional[Dict[str, Any]]:
    """
    Loads a dataset and computes all stats.
    """
    df = load_raw_tabular_data(dataset_id)
    if df is None:
        return None
    
    stats = compute_feature_stats(df)
    stats['dataset_id'] = dataset_id
    return stats

def save_summary_csv(results: List[Dict[str, Any]], output_path: Path, columns: List[str]):
    """
    Saves the results to a CSV file with the specified columns.
    """
    if not results:
        get_logger().warning(f"No results to save for {output_path}")
        # Create an empty file with headers to satisfy downstream checks
        pd.DataFrame(columns=columns).to_csv(output_path, index=False)
        return
    
    df = pd.DataFrame(results)
    # Ensure columns are in order
    if all(col in df.columns for col in columns):
        df = df[columns]
    df.to_csv(output_path, index=False)
    get_logger().info(f"Saved {len(results)} records to {output_path}")

def compute_cardinality():
    """
    Task T024a: Compute cardinality for ALL available datasets.
    Output: data/processed/metadata_stats_cardinality.csv
    """
    get_logger().info("Starting compute_cardinality for all datasets")
    datasets = load_dataset_list()
    results = []
    for ds_id in datasets:
        res = process_single_dataset(ds_id)
        if res:
            results.append(res)
    
    output_path = DATA_PROCESSED_DIR / "metadata_stats_cardinality.csv"
    save_summary_csv(results, output_path, ['dataset_id', 'cardinality'])
    return results

def compute_missingness():
    """
    Task T024b: Compute missingness for ALL available datasets.
    Output: data/processed/metadata_stats_missingness.csv
    """
    get_logger().info("Starting compute_missingness for all datasets")
    datasets = load_dataset_list()
    results = []
    for ds_id in datasets:
        res = process_single_dataset(ds_id)
        if res:
            results.append(res)
    
    output_path = DATA_PROCESSED_DIR / "metadata_stats_missingness.csv"
    save_summary_csv(results, output_path, ['dataset_id', 'missingness'])
    return results

def compute_sparsity():
    """
    Task T024c: Compute sparsity for ALL available datasets.
    Output: data/processed/metadata_stats_sparsity.csv
    """
    get_logger().info("Starting compute_sparsity for all datasets")
    datasets = load_dataset_list()
    results = []
    for ds_id in datasets:
        res = process_single_dataset(ds_id)
        if res:
            results.append(res)
    
    output_path = DATA_PROCESSED_DIR / "metadata_stats_sparsity.csv"
    save_summary_csv(results, output_path, ['dataset_id', 'sparsity'])
    return results

def compute_variance():
    """
    Task T024d: Compute mean variance across all tabular features per dataset for ALL available datasets.
    Output: data/processed/metadata_stats_variance.csv with columns [dataset_id, variance].
    """
    get_logger().info("Starting compute_variance for all datasets")
    datasets = load_dataset_list()
    
    if not datasets:
        get_logger().warning("No datasets found to process for variance.")
        output_path = DATA_PROCESSED_DIR / "metadata_stats_variance.csv"
        save_summary_csv([], output_path, ['dataset_id', 'variance'])
        return []

    results = []
    for ds_id in datasets:
        res = process_single_dataset(ds_id)
        if res:
            results.append({
                'dataset_id': res['dataset_id'],
                'variance': res['variance']
            })
    
    # Sort alphabetically by dataset_id as per general project convention
    results.sort(key=lambda x: x['dataset_id'])
    
    output_path = DATA_PROCESSED_DIR / "metadata_stats_variance.csv"
    save_summary_csv(results, output_path, ['dataset_id', 'variance'])
    get_logger().info(f"Variance computation complete. Output saved to {output_path}")
    return results

def main():
    """
    Main entry point for running variance computation.
    """
    ensure_dir = DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    compute_variance()

if __name__ == "__main__":
    main()