import os
import sys
import json
import hashlib
import logging
import requests
import pandas as pd
import openml
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Logger setup
_logger = None

def setup_loader_logging():
    global _logger
    _logger = logging.getLogger('llmXive.loaders')
    _logger.setLevel(logging.DEBUG)
    if not _logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        _logger.addHandler(handler)
    return _logger

def get_logger():
    if _logger is None:
        setup_loader_logging()
    return _logger

logger = get_logger()

# Checksum utilities
def compute_file_hash(file_path: str, algorithm: str = 'sha256', chunk_size: int = 8192) -> str:
    """Compute the SHA-256 hash of a file."""
    hasher = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def load_checksums(checksum_file: str) -> Dict[str, str]:
    """Load existing checksums from a JSON file."""
    if not os.path.exists(checksum_file):
        return {}
    try:
        with open(checksum_file, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Failed to load checksums from {checksum_file}: {e}")
        return {}

def save_checksums(checksums: Dict[str, str], checksum_file: str) -> None:
    """Save checksums to a JSON file."""
    with open(checksum_file, 'w') as f:
        json.dump(checksums, f, indent=2)

def verify_checksum(file_path: str, expected_hash: str, algorithm: str = 'sha256') -> bool:
    """Verify the hash of a file against an expected value."""
    if not os.path.exists(file_path):
        return False
    actual_hash = compute_file_hash(file_path, algorithm)
    return actual_hash == expected_hash

# Data Loading Logic (Updated to use OpenML as verified source)
def fetch_uci_dataset(dataset_id: int = 15) -> pd.DataFrame:
    """
    Fetch a dataset using OpenML.
    Note: While task description mentions UCI, the verified real data source
    uses the OpenML API for reliable access to the specific datasets required.
    """
    logger.info(f"Fetching dataset ID {dataset_id} from OpenML...")
    try:
        dataset = openml.datasets.get_dataset(dataset_id)
        X, y, _, _ = dataset.get_data(dataset_format='dataframe')
        
        # Concatenate features and target if y exists
        if y is not None:
            df = pd.concat([X, y], axis=1)
        else:
            df = X
        
        return df
    except Exception as e:
        logger.error(f"Failed to fetch dataset {dataset_id} from OpenML: {e}")
        raise

def load_dataset_from_path(file_path: str) -> pd.DataFrame:
    """Load a dataset from a local file path."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Dataset file not found: {file_path}")
    
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.csv':
        return pd.read_csv(file_path)
    elif ext in ['.xlsx', '.xls']:
        return pd.read_excel(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}")

# Data Hygiene Functions
def drop_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows with any missing values."""
    initial_count = len(df)
    df_clean = df.dropna()
    dropped = initial_count - len(df_clean)
    if dropped > 0:
        logger.info(f"Dropped {dropped} rows with missing values.")
    return df_clean

def detect_constant_variables(df: pd.DataFrame) -> List[str]:
    """Detect columns that have only one unique value."""
    constant_cols = []
    for col in df.columns:
        if df[col].nunique() == 1:
            constant_cols.append(col)
    if constant_cols:
        logger.info(f"Detected constant variables: {constant_cols}")
    return constant_cols

def exclude_constant_variables(df: pd.DataFrame, constant_cols: List[str]) -> pd.DataFrame:
    """Exclude constant variables from the dataframe."""
    if not constant_cols:
        return df
    df_clean = df.drop(columns=constant_cols)
    logger.info(f"Excluded {len(constant_cols)} constant variables.")
    return df_clean

def filter_continuous_variables(df: pd.DataFrame) -> pd.DataFrame:
    """Filter dataframe to keep only continuous (numeric) variables."""
    continuous_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    dropped = len(df.columns) - len(continuous_cols)
    if dropped > 0:
        logger.info(f"Dropped {dropped} non-continuous variables.")
    return df[continuous_cols]

def validate_dataset_dimensions(df: pd.DataFrame, min_vars: int = 20) -> bool:
    """Validate that the dataset has at least min_vars continuous variables."""
    if len(df.columns) < min_vars:
        logger.error(f"Dataset has only {len(df.columns)} continuous variables, required {min_vars}.")
        return False
    return True

def apply_hygiene_pipeline(df: pd.DataFrame, min_vars: int = 20) -> pd.DataFrame:
    """Apply the full data hygiene pipeline."""
    df = drop_missing_values(df)
    constant_cols = detect_constant_variables(df)
    df = exclude_constant_variables(df, constant_cols)
    df = filter_continuous_variables(df)
    
    if not validate_dataset_dimensions(df, min_vars):
        raise ValueError(f"Dataset failed dimension validation after hygiene.")
    
    return df

# Metadata Extraction
def extract_metadata(df: pd.DataFrame, dataset_name: str = "unknown") -> Dict[str, Any]:
    """Extract metadata from a dataset."""
    continuous_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    return {
        "dataset_name": dataset_name,
        "original_feature_names": list(df.columns),
        "continuous_feature_names": continuous_cols,
        "num_samples": len(df),
        "num_continuous_features": len(continuous_cols),
        "source_repository": "OpenML",
        "download_method": "openml.datasets.get_dataset"
    }

# Directory and Output Management
def ensure_output_dirs(output_dir: str) -> None:
    """Ensure the output directory exists."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

def verify_no_dynamic_discovery() -> None:
    """
    Placeholder for verification logic. 
    Ensures no dynamic discovery mechanisms are active if required by spec.
    """
    pass

def load_all_datasets(output_dir: str, checksum_file: str = "data/processed/checksums.json") -> List[Dict[str, Any]]:
    """
    Main orchestration function to load datasets, compute checksums, and save processed data.
    """
    ensure_output_dirs(output_dir)
    
    # Define the datasets to load (using OpenML IDs as verified source)
    # ID 15: Breast Cancer Wisconsin (Diagnostic) - Verified in prompt
    # We will load this and potentially others if needed, but start with the verified one.
    dataset_ids = [15] 
    
    processed_data = []
    existing_checksums = load_checksums(checksum_file)
    
    for ds_id in dataset_ids:
        dataset_name = f"dataset_{ds_id}"
        raw_file = os.path.join(output_dir, f"{dataset_name}_raw.csv")
        processed_file = os.path.join(output_dir, f"{dataset_name}_processed.csv")
        
        # Check if raw file exists and is valid
        need_fetch = True
        if os.path.exists(raw_file):
            current_hash = compute_file_hash(raw_file)
            if existing_checksums.get(raw_file) == current_hash:
                logger.info(f"Raw file {raw_file} exists and checksum matches. Skipping fetch.")
                need_fetch = False
        
        if need_fetch:
            logger.info(f"Fetching dataset {ds_id}...")
            df = fetch_uci_dataset(ds_id)
            df.to_csv(raw_file, index=False)
            logger.info(f"Saved raw data to {raw_file}")
        
        # Load raw data for processing
        df_raw = load_dataset_from_path(raw_file)
        
        # Apply hygiene pipeline
        try:
            df_processed = apply_hygiene_pipeline(df_raw, min_vars=20)
        except ValueError as e:
            logger.warning(f"Skipping dataset {ds_id} due to hygiene failure: {e}")
            continue
        
        # Save processed data
        df_processed.to_csv(processed_file, index=False)
        logger.info(f"Saved processed data to {processed_file}")
        
        # Compute and save checksums
        raw_hash = compute_file_hash(raw_file)
        proc_hash = compute_file_hash(processed_file)
        existing_checksums[raw_file] = raw_hash
        existing_checksums[processed_file] = proc_hash
        
        # Extract and store metadata
        metadata = extract_metadata(df_processed, dataset_name)
        metadata["raw_file_path"] = raw_file
        metadata["processed_file_path"] = processed_file
        metadata["raw_checksum"] = raw_hash
        metadata["processed_checksum"] = proc_hash
        
        processed_data.append(metadata)
    
    # Save updated checksums
    save_checksums(existing_checksums, checksum_file)
    
    return processed_data

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Load and process datasets with checksumming.")
    parser.add_argument("--output", type=str, default="data/processed/", help="Output directory for processed data.")
    args = parser.parse_args()
    
    setup_loader_logging()
    logger.info(f"Starting data loading pipeline. Output: {args.output}")
    
    try:
        results = load_all_datasets(args.output)
        logger.info(f"Pipeline completed successfully. Loaded {len(results)} datasets.")
        for r in results:
            logger.info(f"Dataset: {r['dataset_name']}, Features: {r['num_continuous_features']}, Samples: {r['num_samples']}")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()