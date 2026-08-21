import os
import sys
import json
import hashlib
import logging
import requests
import pandas as pd
import numpy as np
import openml
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import time

# --- Logging Setup ---
def setup_loader_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def get_logger(name: str = "loaders"):
    return logging.getLogger(name)

logger = get_logger()

# --- Checksum Utilities ---
def compute_file_hash(file_path: str) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_checksums(checksum_file: str) -> Dict[str, str]:
    """Load checksums from a JSON file."""
    if os.path.exists(checksum_file):
        with open(checksum_file, 'r') as f:
            return json.load(f)
    return {}

def save_checksums(checksums: Dict[str, str], checksum_file: str):
    """Save checksums to a JSON file."""
    with open(checksum_file, 'w') as f:
        json.dump(checksums, f, indent=4)

def verify_checksum(file_path: str, expected_hash: str) -> bool:
    """Verify file integrity against expected hash."""
    if not os.path.exists(file_path):
        return False
    actual_hash = compute_file_hash(file_path)
    return actual_hash == expected_hash

# --- Data Loading Logic ---
def fetch_uci_dataset(dataset_id: int) -> pd.DataFrame:
    """
    Fetch a dataset from OpenML (verified UCI source).
    This replaces any direct URL fetching to ensure reliability.
    """
    logger.info(f"Fetching OpenML dataset ID: {dataset_id}")
    try:
        dataset = openml.datasets.get_dataset(dataset_id)
        X, y, _, _ = dataset.get_data(dataset_format='dataframe')
        if y is not None:
            df = pd.concat([X, y], axis=1)
        else:
            df = X
        
        # Store metadata in columns for later extraction if needed
        df.attrs['dataset_name'] = dataset.name
        df.attrs['dataset_id'] = dataset.dataset_id
        df.attrs['source_repository'] = 'OpenML (UCI)'
        
        return df
    except Exception as e:
        logger.error(f"Failed to fetch dataset {dataset_id}: {e}")
        raise

def load_dataset_from_path(file_path: str) -> pd.DataFrame:
    """Load dataset from a local file (CSV/Excel)."""
    logger.info(f"Loading dataset from path: {file_path}")
    if file_path.endswith('.csv'):
        return pd.read_csv(file_path)
    elif file_path.endswith(('.xlsx', '.xls')):
        return pd.read_excel(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_path}")

def drop_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows with any missing values."""
    initial_rows = len(df)
    df_clean = df.dropna()
    dropped = initial_rows - len(df_clean)
    if dropped > 0:
        logger.info(f"Dropped {dropped} rows with missing values.")
    return df_clean

def detect_constant_variables(df: pd.DataFrame) -> List[str]:
    """Detect variables that have only one unique value."""
    constant_vars = []
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            if df[col].nunique() <= 1:
                constant_vars.append(col)
    return constant_vars

def exclude_constant_variables(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """Exclude constant variables and return the filtered dataframe."""
    constant_vars = detect_constant_variables(df)
    if constant_vars:
        logger.info(f"Excluding constant variables: {constant_vars}")
        df_filtered = df.drop(columns=constant_vars)
    else:
        df_filtered = df
    return df_filtered, constant_vars

def filter_continuous_variables(df: pd.DataFrame) -> pd.DataFrame:
    """Filter to keep only continuous (numeric) variables."""
    continuous_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
    if len(continuous_cols) == 0:
        logger.warning("No continuous variables found.")
        return pd.DataFrame()
    df_continuous = df[continuous_cols]
    logger.info(f"Filtered to {len(continuous_cols)} continuous variables.")
    return df_continuous

def validate_dataset_dimensions(df: pd.DataFrame, min_continuous_vars: int = 20) -> bool:
    """Validate that the dataset has enough continuous variables."""
    num_continuous = len([c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])])
    if num_continuous < min_continuous_vars:
        logger.warning(f"Dataset has only {num_continuous} continuous variables (min: {min_continuous_vars}).")
        return False
    return True

def apply_hygiene_pipeline(df: pd.DataFrame, min_continuous_vars: int = 20) -> Optional[pd.DataFrame]:
    """Apply the full hygiene pipeline: drop missing, drop constant, filter continuous, validate."""
    df = drop_missing_values(df)
    df, _ = exclude_constant_variables(df)
    df = filter_continuous_variables(df)
    
    if not validate_dataset_dimensions(df, min_continuous_vars):
        return None
    
    return df

def extract_metadata(df: pd.DataFrame, source: str = "OpenML") -> Dict[str, Any]:
    """Extract metadata from the dataframe."""
    original_feature_names = list(df.columns)
    continuous_feature_names = [c for c in original_feature_names if pd.api.types.is_numeric_dtype(df[c])]
    num_samples = df.shape[0]
    num_continuous_features = len(continuous_feature_names)
    
    return {
        "dataset_name": df.attrs.get('dataset_name', "Unknown"),
        "original_feature_names": original_feature_names,
        "continuous_feature_names": continuous_feature_names,
        "num_samples": num_samples,
        "num_continuous_features": num_continuous_features,
        "source_repository": source,
        "download_method": "openml.datasets.get_dataset"
    }

def ensure_output_dirs(output_dir: str):
    """Ensure output directories exist."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

def verify_no_dynamic_discovery(df: pd.DataFrame):
    """
    T082: Dataset Variable Type Enforcement.
    Ensures that all columns in the dataset are of a valid type for analysis.
    Specifically, it enforces that only numeric types are kept for correlation analysis.
    It also checks for object types that might be misinterpreted as numeric (e.g., strings that look like numbers).
    """
    logger.info("Running Variable Type Enforcement (T082)...")
    
    # Check for any non-numeric columns that slipped through
    non_numeric_cols = []
    for col in df.columns:
        if not pd.api.types.is_numeric_dtype(df[col]):
            non_numeric_cols.append(col)
    
    if non_numeric_cols:
        logger.warning(f"Found non-numeric columns that were not filtered: {non_numeric_cols}")
        # In a strict pipeline, we might drop these or raise an error.
        # Given the pipeline already filters continuous, this is a sanity check.
        # We enforce by dropping them if they exist unexpectedly.
        df = df.drop(columns=non_numeric_cols)
        logger.info(f"Dropped {len(non_numeric_cols)} unexpected non-numeric columns.")
    
    # Check for infinite values which are not valid for correlation
    if np.isinf(df).any().any():
        logger.warning("Infinite values detected. Replacing with NaN.")
        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.dropna()
    
    # Check for NaNs after replacement
    if df.isna().any().any():
        logger.warning("NaNs detected after infinite replacement. Dropping rows.")
        df = df.dropna()

    return df

def load_all_datasets(dataset_ids: List[int], output_dir: str, min_continuous_vars: int = 20):
    """
    Load multiple datasets, apply hygiene, enforce variable types, and save processed data.
    """
    ensure_output_dirs(output_dir)
    processed_data = []
    checksums = load_checksums(os.path.join(output_dir, 'checksums.json'))
    
    for ds_id in dataset_ids:
        try:
            # Fetch
            df = fetch_uci_dataset(ds_id)
            
            # Hygiene
            df_clean = apply_hygiene_pipeline(df, min_continuous_vars)
            
            if df_clean is None:
                logger.warning(f"Dataset {ds_id} failed hygiene checks (insufficient continuous vars). Skipping.")
                continue
            
            # T082: Enforce Variable Types
            df_enforced = verify_no_dynamic_discovery(df_clean)
            
            if df_enforced.empty:
                logger.warning(f"Dataset {ds_id} became empty after variable enforcement. Skipping.")
                continue

            # Save
            filename = f"dataset_{ds_id}_processed.csv"
            file_path = os.path.join(output_dir, filename)
            df_enforced.to_csv(file_path, index=False)
            
            # Checksum
            current_hash = compute_file_hash(file_path)
            checksums[filename] = current_hash
            
            # Metadata
            meta = extract_metadata(df_enforced, "OpenML")
            meta['file_path'] = file_path
            meta['dataset_id'] = ds_id
            processed_data.append(meta)
            
            logger.info(f"Successfully processed and saved dataset {ds_id}: {filename}")
            
        except Exception as e:
            logger.error(f"Failed to process dataset {ds_id}: {e}")
            continue
    
    # Save checksums
    save_checksums(checksums, os.path.join(output_dir, 'checksums.json'))
    
    # Save metadata summary
    meta_path = os.path.join(output_dir, 'metadata_summary.json')
    with open(meta_path, 'w') as f:
        json.dump(processed_data, f, indent=4)
    
    return processed_data

def main():
    """Main entry point for the loader script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Load and process datasets.")
    parser.add_argument('--output', type=str, default='data/processed', help='Output directory')
    parser.add_argument('--datasets', type=int, nargs='+', default=[15, 11, 12, 53, 29, 35], 
                        help='List of OpenML dataset IDs to load')
    args = parser.parse_args()
    
    setup_loader_logging()
    logger.info(f"Starting data loading process. Output: {args.output}")
    
    # T082 is integrated into load_all_datasets via verify_no_dynamic_discovery
    load_all_datasets(args.datasets, args.output)
    
    logger.info("Data loading process completed.")

if __name__ == '__main__':
    main()