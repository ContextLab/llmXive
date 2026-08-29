"""
Pipeline: Normalize Tabular Features (T024f)

Implements:
- Load raw tabular data for ALL available datasets.
- Apply standard normalization (z-score) per feature using global mean/std.
- Handle missing values via mean imputation.
- Output: data/processed/normalized_tabular_features.parquet

Dependency: T045 (Data Integrity Check) and T045b (Imputation Strategy) must have run.
Canonical Function: code/utils/feature_engineering.py::normalize_features
"""
import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

import pandas as pd
import pyarrow.parquet as pq
from utils.logging import get_logger, log_info, log_warning, log_error, log_debug
from utils.feature_engineering import normalize_features, save_normalization_metadata
from config import ensure_directories

logger = get_logger(__name__)

def load_raw_tabular_data(data_dir: Path) -> List[pd.DataFrame]:
    """
    Loads all raw tabular CSV files from the data directory.
    Expects files in data/raw/ or subdirectories.
    Returns a list of DataFrames, each with a 'dataset_id' column added.
    """
    raw_dir = data_dir / "raw"
    if not raw_dir.exists():
        log_error(f"Raw data directory not found: {raw_dir}")
        raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")

    dfs = []
    csv_files = list(raw_dir.glob("*.csv"))
    
    if not csv_files:
        log_error(f"No CSV files found in {raw_dir}")
        raise FileNotFoundError(f"No CSV files found in {raw_dir}")

    log_info(f"Found {len(csv_files)} CSV files in {raw_dir}")

    for file_path in csv_files:
        # Skip the baselines file as it is not raw feature data for normalization
        if "multabench_baselines.csv" in file_path.name:
            log_debug(f"Skipping baseline file: {file_path.name}")
            continue

        try:
            df = pd.read_csv(file_path)
            dataset_id = file_path.stem
            
            # Ensure dataset_id column exists
            if 'dataset_id' not in df.columns:
                df['dataset_id'] = dataset_id
            
            # Basic validation
            if df.empty:
                log_warning(f"Dataset {dataset_id} is empty. Skipping.")
                continue
            
            log_info(f"Loaded dataset {dataset_id} with shape {df.shape}")
            dfs.append(df)
        except Exception as e:
            log_error(f"Failed to load {file_path}: {e}")
            # Continue processing other datasets rather than failing immediately
            continue

    if not dfs:
        log_error("No valid datasets loaded.")
        raise ValueError("No valid datasets loaded.")

    return dfs

def process_all_datasets(dfs: List[pd.DataFrame], method: str = "zscore") -> pd.DataFrame:
    """
    Processes all loaded datasets: concatenates, normalizes, and handles missing values.
    Uses global statistics calculated across the combined dataset for consistency.
    """
    if not dfs:
        raise ValueError("No datasets to process.")

    log_info(f"Concatenating {len(dfs)} datasets...")
    combined_df = pd.concat(dfs, ignore_index=True)
    log_info(f"Combined dataset shape: {combined_df.shape}")

    # Separate metadata columns from numeric features
    # We assume 'dataset_id' is the only non-numeric metadata column for this task
    # If there are others, they should be handled or excluded here.
    numeric_cols = combined_df.select_dtypes(include=['number']).columns.tolist()
    
    if 'dataset_id' in numeric_cols:
        numeric_cols.remove('dataset_id')
    
    if not numeric_cols:
        log_error("No numeric feature columns found for normalization.")
        raise ValueError("No numeric feature columns found.")

    log_info(f"Normalizing {len(numeric_cols)} features using method: {method}")
    
    # Extract the numeric features for normalization
    features_df = combined_df[numeric_cols].copy()
    
    # Apply normalization
    normalized_features, metadata = normalize_features(features_df, method=method)
    
    # Reattach dataset_id and any other non-numeric columns if they existed
    # For this specific task, we focus on the normalized features + dataset_id
    result_df = pd.concat([combined_df[['dataset_id']], normalized_features], axis=1)
    
    # Save normalization metadata for downstream tasks (T019d, T025)
    metadata_path = Path("data/processed/normalization_metadata.json")
    ensure_directories([metadata_path])
    save_normalization_metadata(metadata, metadata_path)
    
    log_info(f"Normalization complete. Metadata saved to {metadata_path}")
    
    return result_df

def save_to_parquet(df: pd.DataFrame, output_path: Path):
    """
    Saves the normalized DataFrame to a Parquet file.
    """
    ensure_directories([output_path])
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_parquet(output_path, index=False)
    log_info(f"Saved normalized features to {output_path}")
    
    # Verify file size
    size_mb = output_path.stat().st_size / (1024 * 1024)
    log_info(f"Output file size: {size_mb:.2f} MB")

def main():
    parser = argparse.ArgumentParser(description="Normalize tabular features for all datasets.")
    parser.add_argument("--data-dir", type=str, default="data", help="Root data directory")
    parser.add_argument("--output", type=str, default="data/processed/normalized_tabular_features.parquet", help="Output Parquet path")
    parser.add_argument("--method", type=str, default="zscore", choices=["zscore", "minmax"], help="Normalization method")
    args = parser.parse_args()

    log_info("Starting normalization pipeline (T024f)...")
    
    data_dir = Path(args.data_dir)
    output_path = Path(args.output)

    try:
        # 1. Load raw data
        dfs = load_raw_tabular_data(data_dir)
        
        # 2. Process and normalize
        normalized_df = process_all_datasets(dfs, method=args.method)
        
        # 3. Save output
        save_to_parquet(normalized_df, output_path)
        
        log_info("Normalization pipeline completed successfully.")
        
    except FileNotFoundError as e:
        log_error(f"Data loading failed: {e}")
        sys.exit(1)
    except ValueError as e:
        log_error(f"Processing failed: {e}")
        sys.exit(1)
    except Exception as e:
        log_error(f"Unexpected error: {e}")
        import traceback
        log_error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
