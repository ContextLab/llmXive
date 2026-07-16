import pandas as pd
import numpy as np
from typing import List, Tuple, Optional, Dict, Any
import requests
from io import StringIO
import os
import json
import hashlib
import logging
import sys

# Configure logging for the loader module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('output/logs/loader.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Import config for paths and dataset definitions
try:
    from config import get_config, ensure_dirs
except ImportError:
    # Fallback for direct execution or missing config import context
    def get_config():
        return {
            'paths': {
                'raw': 'data/raw',
                'processed': 'data/processed',
                'results': 'output/results',
                'plots': 'output/plots',
                'reports': 'output/reports',
                'exploratory': 'output/exploratory',
                'logs': 'output/logs'
            },
            'datasets': {
                'wine': {
                    'url': 'https://archive.ics.uci.edu/ml/machine-learning-databases/wine/wine.data',
                    'filename': 'wine.data'
                },
                'abalone': {
                    'url': 'https://archive.ics.uci.edu/ml/machine-learning-databases/abalone/abalone.data',
                    'filename': 'abalone.data'
                },
                'breast_cancer': {
                    'url': 'https://archive.ics.uci.edu/ml/machine-learning-databases/breast-cancer-wisconsin/breast-cancer-wisconsin.data',
                    'filename': 'breast-cancer-wisconsin.data'
                },
                'student_performance': {
                    'url': 'https://archive.ics.uci.edu/ml/machine-learning-databases/student/student-por.csv',
                    'filename': 'student-por.csv'
                },
                'air_quality': {
                    'url': 'https://archive.ics.uci.edu/ml/machine-learning-databases/00360/AirQualityUCI.zip',
                    'filename': 'AirQualityUCI.zip' # Note: Actual ingestion might need unzip logic, simplified here to URL fetch
                },
                'concrete': {
                    'url': 'https://archive.ics.uci.edu/ml/machine-learning-databases/concrete/compressive/strength.csv',
                    'filename': 'strength.csv'
                }
            },
            'random_seed': 42
        }

def ensure_dirs(paths: Dict[str, str]) -> None:
    """Ensure all required directories exist."""
    for path in paths.values():
        os.makedirs(path, exist_ok=True)

def compute_file_hash(filepath: str, algorithm: str = 'sha256') -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_checksums(checksum_file: str) -> Dict[str, str]:
    """Load existing checksums from JSON file."""
    if os.path.exists(checksum_file):
        with open(checksum_file, 'r') as f:
            return json.load(f)
    return {}

def save_checksums(checksums: Dict[str, str], checksum_file: str) -> None:
    """Save checksums to JSON file."""
    with open(checksum_file, 'w') as f:
        json.dump(checksums, f, indent=2)

def verify_checksum(filepath: str, expected_hash: str) -> bool:
    """Verify file integrity against expected hash."""
    if not os.path.exists(filepath):
        return False
    actual_hash = compute_file_hash(filepath)
    return actual_hash == expected_hash

def fetch_uci_dataset(dataset_name: str, raw_dir: str) -> str:
    """
    Fetch a dataset from a verified UCI URL.
    Raises FileNotFoundError if download fails.
    """
    config = get_config()
    if dataset_name not in config['datasets']:
        raise ValueError(f"Dataset {dataset_name} not found in config.")

    dataset_info = config['datasets'][dataset_name]
    url = dataset_info['url']
    filename = dataset_info['filename']
    filepath = os.path.join(raw_dir, filename)

    if os.path.exists(filepath):
        logger.info(f"Dataset {dataset_name} already exists at {filepath}")
        # Optional: Verify checksum if available
        checksums = load_checksums(os.path.join(raw_dir, 'checksums.json'))
        if filename in checksums:
            if verify_checksum(filepath, checksums[filename]):
                logger.info(f"Checksum verified for {filename}")
            else:
                logger.warning(f"Checksum mismatch for {filename}, re-downloading...")
                os.remove(filepath)
        else:
            logger.warning(f"No checksum found for {filename}, skipping verification")
        return filepath

    logger.info(f"Downloading {dataset_name} from {url}...")
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        # Handle different content types
        if 'text' in response.headers.get('Content-Type', '') or 'csv' in filename:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(response.text)
        else:
            # Binary write for zips or other formats
            with open(filepath, 'wb') as f:
                f.write(response.content)
        
        # Save checksum
        checksums = load_checksums(os.path.join(raw_dir, 'checksums.json'))
        new_hash = compute_file_hash(filepath)
        checksums[filename] = new_hash
        save_checksums(checksums, os.path.join(raw_dir, 'checksums.json'))
        logger.info(f"Successfully downloaded and saved {filename} with hash {new_hash[:16]}...")
        return filepath
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download {dataset_name}: {e}")
        raise FileNotFoundError(f"Could not fetch dataset {dataset_name} from {url}") from e

def load_dataset_from_path(filepath: str, dataset_name: str = None) -> pd.DataFrame:
    """Load dataset from a local path, handling headers and delimiters."""
    try:
        # Attempt to load as CSV, auto-detect delimiter if needed
        # UCI datasets often have specific formats
        if dataset_name == 'wine':
            # Wine dataset has no header, comma-separated
            df = pd.read_csv(filepath, header=None, sep=',')
        elif dataset_name == 'abalone':
            # Abalone has no header, comma-separated
            df = pd.read_csv(filepath, header=None, sep=',')
        elif dataset_name == 'breast_cancer':
            # Breast Cancer has no header, comma-separated
            df = pd.read_csv(filepath, header=None, sep=',')
        elif dataset_name == 'student_performance':
            # Student performance has header, semicolon-separated
            df = pd.read_csv(filepath, header=0, sep=';')
        elif dataset_name == 'air_quality':
            # Air Quality is complex, often needs specific parsing. 
            # For this pipeline, we assume a simplified CSV extraction or skip if not supported.
            # Placeholder for specific parsing logic if needed.
            df = pd.read_csv(filepath, sep=';', decimal=',', header=0)
        elif dataset_name == 'concrete':
            # Concrete has header, comma-separated
            df = pd.read_csv(filepath, header=0, sep=',')
        else:
            # Default attempt
            df = pd.read_csv(filepath)
        
        logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns from {filepath}")
        return df
    except Exception as e:
        logger.error(f"Failed to load dataset from {filepath}: {e}")
        raise

def drop_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows with any missing values."""
    initial_count = len(df)
    df_clean = df.dropna()
    dropped_count = initial_count - len(df_clean)
    if dropped_count > 0:
        logger.info(f"Dropped {dropped_count} rows with missing values ({dropped_count/initial_count*100:.2f}%)")
    return df_clean

def detect_constant_variables(df: pd.DataFrame) -> List[str]:
    """
    Detect and log constant variables (zero variance).
    Returns a list of column names that are constant.
    """
    constant_vars = []
    for col in df.columns:
        if df[col].nunique() == 1:
            constant_vars.append(col)
        elif pd.api.types.is_numeric_dtype(df[col]) and df[col].var() == 0:
            # Explicit check for zero variance on numeric types
            constant_vars.append(col)
    
    if constant_vars:
        logger.info(f"Detected {len(constant_vars)} constant variables: {', '.join(constant_vars)}")
    else:
        logger.info("No constant variables detected.")
    
    return constant_vars

def exclude_constant_variables(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Exclude constant variables from the DataFrame.
    Returns the cleaned DataFrame and a list of dropped column names.
    """
    constant_vars = detect_constant_variables(df)
    if constant_vars:
        df_clean = df.drop(columns=constant_vars)
        logger.info(f"Excluded {len(constant_vars)} constant variables from analysis.")
        return df_clean, constant_vars
    return df, []

def filter_continuous_variables(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter to keep only continuous (numeric) variables.
    """
    initial_cols = len(df.columns)
    df_numeric = df.select_dtypes(include=[np.number])
    dropped_cols = initial_cols - len(df_numeric.columns)
    if dropped_cols > 0:
        logger.info(f"Dropped {dropped_cols} non-numeric columns.")
    return df_numeric

def validate_dataset_dimensions(df: pd.DataFrame, min_rows: int = 20, min_cols: int = 2) -> bool:
    """
    Validate that the dataset meets minimum size requirements.
    """
    if len(df) < min_rows:
        logger.error(f"Dataset has only {len(df)} rows, minimum required is {min_rows}.")
        return False
    if len(df.columns) < min_cols:
        logger.error(f"Dataset has only {len(df.columns)} columns, minimum required is {min_cols}.")
        return False
    return True

def apply_hygiene_pipeline(df: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
    """
    Apply full data hygiene pipeline:
    1. Drop missing values
    2. Detect and exclude constant variables (with logging)
    3. Filter to continuous variables
    4. Validate dimensions
    """
    logger.info(f"Starting hygiene pipeline for {dataset_name}...")
    
    # Step 1: Drop missing
    df = drop_missing_values(df)
    
    # Step 2: Exclude constant variables (T046 requirement: explicit logging)
    df, dropped_constant = exclude_constant_variables(df)
    
    # Step 3: Filter continuous
    df = filter_continuous_variables(df)
    
    # Step 4: Validate
    if not validate_dataset_dimensions(df, min_rows=20, min_cols=2):
        raise ValueError(f"Dataset {dataset_name} failed dimension validation after hygiene.")
    
    logger.info(f"Hygiene pipeline complete for {dataset_name}. Final shape: {df.shape}")
    return df

def load_and_hygiene_dataset(dataset_name: str, raw_dir: str, processed_dir: str) -> pd.DataFrame:
    """
    Load a dataset, apply hygiene, and save to processed directory.
    """
    # Fetch
    filepath = fetch_uci_dataset(dataset_name, raw_dir)
    
    # Load
    df = load_dataset_from_path(filepath, dataset_name)
    
    # Hygiene
    df_clean = apply_hygiene_pipeline(df, dataset_name)
    
    # Save
    output_filename = f"{dataset_name}_cleaned.csv"
    output_path = os.path.join(processed_dir, output_filename)
    df_clean.to_csv(output_path, index=False)
    logger.info(f"Saved cleaned dataset to {output_path}")
    
    return df_clean

def main():
    """
    Main entry point for running the loader pipeline on all configured datasets.
    Usage: python code/loaders.py --output data/processed/
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Load and clean UCI datasets.')
    parser.add_argument('--output', type=str, default='data/processed/', help='Output directory for processed data.')
    args = parser.parse_args()
    
    config = get_config()
    ensure_dirs(config['paths'])
    
    processed_dir = args.output
    raw_dir = config['paths']['raw']
    
    logger.info(f"Starting dataset loading pipeline. Output: {processed_dir}")
    
    for dataset_name in config['datasets'].keys():
        try:
            df = load_and_hygiene_dataset(dataset_name, raw_dir, processed_dir)
            logger.info(f"Successfully processed {dataset_name}. Shape: {df.shape}")
        except Exception as e:
            logger.error(f"Failed to process {dataset_name}: {e}")
            # Continue with other datasets, but log the failure
            continue
    
    logger.info("Dataset loading pipeline completed.")

if __name__ == "__main__":
    main()