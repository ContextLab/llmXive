import os
import sys
import json
import hashlib
import logging
import requests
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
import numpy as np
import openpyxl

from config import get_config, ensure_dirs

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_loader_logging():
    """Setup logging for the loader module."""
    logger.setLevel(logging.INFO)
    logger.info("Loader module logging initialized.")

def load_checksums(checksum_path: str) -> Dict[str, str]:
    """Load existing checksums from a JSON file."""
    if os.path.exists(checksum_path):
        with open(checksum_path, 'r') as f:
            return json.load(f)
    return {}

def save_checksums(checksums: Dict[str, str], checksum_path: str) -> None:
    """Save checksums to a JSON file."""
    os.makedirs(os.path.dirname(checksum_path), exist_ok=True)
    with open(checksum_path, 'w') as f:
        json.dump(checksums, f, indent=2)

def compute_file_hash(file_path: str) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: str, expected_hash: str) -> bool:
    """Verify file hash against expected value."""
    actual_hash = compute_file_hash(file_path)
    return actual_hash == expected_hash

def fetch_uci_dataset(url: str, dest_path: str, dataset_name: str, checksums: Dict[str, str]) -> str:
    """Fetch dataset from UCI repository."""
    if os.path.exists(dest_path):
        logger.info(f"Dataset {dataset_name} already exists at {dest_path}")
        # Verify checksum if available
        if dataset_name in checksums:
            if verify_checksum(dest_path, checksums[dataset_name]):
                logger.info(f"Checksum verified for {dataset_name}")
                return dest_path
            else:
                logger.warning(f"Checksum mismatch for {dataset_name}, re-downloading...")
        else:
            # Compute and store checksum if not known
            computed_hash = compute_file_hash(dest_path)
            checksums[dataset_name] = computed_hash
            logger.info(f"Computed and stored checksum for {dataset_name}: {computed_hash}")
            return dest_path
    
    logger.info(f"Downloading {dataset_name} from {url}")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Compute and store checksum
        computed_hash = compute_file_hash(dest_path)
        checksums[dataset_name] = computed_hash
        logger.info(f"Downloaded and checksummed {dataset_name}: {computed_hash}")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download {dataset_name}: {e}")
        raise FileNotFoundError(f"Could not fetch dataset {dataset_name} from {url}")
    
    return dest_path

def load_dataset_from_path(file_path: str, sep: str = ',', engine: Optional[str] = None) -> pd.DataFrame:
    """Load dataset from a file path, handling different formats."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    logger.info(f"Loading dataset from {file_path}")
    
    try:
        # Handle Excel files (.xls, .xlsx)
        if file_path.lower().endswith(('.xls', '.xlsx')):
            logger.info(f"Loading Excel file: {file_path}")
            df = pd.read_excel(file_path, engine='openpyxl')
        # Handle CSV files
        elif file_path.lower().endswith('.csv'):
            logger.info(f"Loading CSV file: {file_path}")
            df = pd.read_csv(file_path, sep=sep, engine=engine)
        else:
            # Try to infer format
            logger.warning(f"Unknown file format, attempting CSV load: {file_path}")
            df = pd.read_csv(file_path, sep=sep, engine=engine)
        
        logger.info(f"Loaded dataset with shape: {df.shape}")
        return df
        
    except Exception as e:
        logger.error(f"Failed to load dataset from {file_path}: {e}")
        raise

def drop_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows with any missing values."""
    initial_rows = len(df)
    df_clean = df.dropna()
    dropped_rows = initial_rows - len(df_clean)
    if dropped_rows > 0:
        logger.warning(f"Dropped {dropped_rows} rows with missing values")
    return df_clean

def detect_constant_variables(df: pd.DataFrame) -> List[str]:
    """Detect columns with zero variance (constant values)."""
    constant_cols = []
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            if df[col].nunique() <= 1:
                constant_cols.append(col)
        else:
            # Non-numeric columns are treated as constant for correlation analysis
            constant_cols.append(col)
    return constant_cols

def exclude_constant_variables(df: pd.DataFrame, constant_cols: List[str]) -> pd.DataFrame:
    """Drop constant columns from the dataframe."""
    if constant_cols:
        logger.info(f"Dropping constant columns: {constant_cols}")
        df = df.drop(columns=constant_cols)
    return df

def filter_continuous_variables(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only continuous (numeric) variables."""
    initial_cols = len(df.columns)
    df_continuous = df.select_dtypes(include=[np.number])
    dropped_cols = initial_cols - len(df_continuous.columns)
    if dropped_cols > 0:
        logger.warning(f"Dropped {dropped_cols} non-continuous columns")
    return df_continuous

def validate_dataset_dimensions(df: pd.DataFrame, min_vars: int = 20) -> bool:
    """Validate that dataset has at least min_vars continuous variables."""
    if len(df.columns) < min_vars:
        logger.error(f"Dataset has only {len(df.columns)} continuous variables, required {min_vars}")
        return False
    return True

def apply_hygiene_pipeline(df: pd.DataFrame, min_vars: int = 20) -> Tuple[pd.DataFrame, bool]:
    """Apply full data hygiene pipeline."""
    # Drop missing values
    df = drop_missing_values(df)
    
    # Detect and drop constant variables
    constant_cols = detect_constant_variables(df)
    df = exclude_constant_variables(df, constant_cols)
    
    # Keep only continuous variables
    df = filter_continuous_variables(df)
    
    # Validate dimensions
    is_valid = validate_dataset_dimensions(df, min_vars)
    
    return df, is_valid

def load_and_hygiene_dataset(url: str, dest_path: str, dataset_name: str, 
                             checksums: Dict[str, str], min_vars: int = 20,
                             sep: str = ',', engine: Optional[str] = None) -> Optional[pd.DataFrame]:
    """Load dataset and apply hygiene pipeline."""
    try:
        # Fetch dataset
        local_path = fetch_uci_dataset(url, dest_path, dataset_name, checksums)
        
        # Load dataset
        df = load_dataset_from_path(local_path, sep=sep, engine=engine)
        
        # Apply hygiene
        df_clean, is_valid = apply_hygiene_pipeline(df, min_vars)
        
        if not is_valid:
            return None
        
        return df_clean
        
    except Exception as e:
        logger.error(f"Failed to load and process {dataset_name}: {e}")
        return None

def load_all_datasets(config: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
    """Load all datasets defined in config."""
    datasets = {}
    checksums_path = os.path.join(config['data_raw'], 'checksums.json')
    checksums = load_checksums(checksums_path)
    
    for dataset_name, dataset_info in config['datasets'].items():
        url = dataset_info['url']
        dest_path = os.path.join(config['data_raw'], f"{dataset_name}.raw")
        
        # Handle special cases for file extensions
        if 'extension' in dataset_info:
            ext = dataset_info['extension']
            if ext.lower() in ['.xls', '.xlsx']:
                dest_path = os.path.join(config['data_raw'], f"{dataset_name}{ext}")
        
        df = load_and_hygiene_dataset(
            url=url,
            dest_path=dest_path,
            dataset_name=dataset_name,
            checksums=checksums,
            min_vars=config.get('min_continuous_vars', 20),
            sep=dataset_info.get('sep', ','),
            engine=dataset_info.get('engine')
        )
        
        if df is not None:
            datasets[dataset_name] = df
            logger.info(f"Successfully loaded and processed {dataset_name}")
        else:
            logger.warning(f"Skipped {dataset_name} due to validation failure")
    
    # Save updated checksums
    save_checksums(checksums, checksums_path)
    
    return datasets

def ensure_output_dirs(config: Dict[str, Any]) -> None:
    """Ensure all output directories exist."""
    ensure_dirs(config)

def verify_no_dynamic_discovery(datasets: Dict[str, pd.DataFrame], config: Dict[str, Any]) -> bool:
    """Verify that only configured datasets were loaded."""
    expected_datasets = set(config['datasets'].keys())
    loaded_datasets = set(datasets.keys())
    
    if loaded_datasets != expected_datasets:
        missing = expected_datasets - loaded_datasets
        if missing:
            logger.warning(f"Missing expected datasets: {missing}")
        return False
    return True

def main():
    """Main entry point for loader script."""
    parser = argparse.ArgumentParser(description="Load and process datasets")
    parser.add_argument('--output', type=str, default=None, 
                      help='Output directory for processed data')
    parser.add_argument('--config', type=str, default=None,
                      help='Path to config file (optional)')
    
    args = parser.parse_args()
    
    setup_loader_logging()
    
    # Load config
    config = get_config()
    if args.output:
        config['data_processed'] = args.output
    
    # Ensure directories
    ensure_output_dirs(config)
    
    # Load datasets
    datasets = load_all_datasets(config)
    
    if not datasets:
        logger.error("No datasets were successfully loaded")
        sys.exit(1)
    
    logger.info(f"Successfully loaded {len(datasets)} datasets")
    
    # Verify no dynamic discovery
    if not verify_no_dynamic_discovery(datasets, config):
        logger.warning("Dynamic discovery detected or expected datasets missing")
    
    # Save processed datasets
    for name, df in datasets.items():
        output_path = os.path.join(config['data_processed'], f"{name}_processed.csv")
        df.to_csv(output_path, index=False)
        logger.info(f"Saved processed dataset {name} to {output_path}")
    
    logger.info("Dataset loading and processing complete")

if __name__ == "__main__":
    main()