import pandas as pd
import numpy as np
from typing import List, Tuple, Optional, Dict, Any
import requests
from io import StringIO
import os
import hashlib
import json
import logging
import sys
from pathlib import Path

# Import config for paths and dataset definitions
# We assume config.py is in the same directory or PYTHONPATH
try:
    from config import get_config, ensure_dirs
except ImportError:
    # Fallback for direct execution or different import structure
    import config
    get_config = config.get_config
    ensure_dirs = config.ensure_dirs

# --- Logging Setup ---
# Fix for T061/Execution Failure: Ensure log directory exists before creating handler
def setup_loader_logging():
    config = get_config()
    log_dir = Path(config['paths']['logs'])
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / 'loader.log'
    
    logger = logging.getLogger('loaders')
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers to avoid duplicates in interactive environments
    if not logger.handlers:
        fh = logging.FileHandler(log_file, mode='a')
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    
    return logger

logger = setup_loader_logging()

# --- Checksum Utilities (T035 Implementation) ---

def compute_file_hash(file_path: str, algorithm: str = 'sha256') -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_checksums(checksum_file: str) -> Dict[str, str]:
    """Load existing checksums from JSON file."""
    if os.path.exists(checksum_file):
        with open(checksum_file, 'r') as f:
            return json.load(f)
    return {}

def save_checksums(checksums: Dict[str, str], checksum_file: str):
    """Save checksums to JSON file."""
    Path(checksum_file).parent.mkdir(parents=True, exist_ok=True)
    with open(checksum_file, 'w') as f:
        json.dump(checksums, f, indent=2)

def verify_checksum(file_path: str, expected_hash: str) -> bool:
    """Verify file integrity against expected hash."""
    if not os.path.exists(file_path):
        return False
    actual_hash = compute_file_hash(file_path)
    return actual_hash == expected_hash

# --- Dataset Definitions (From T004) ---
# These are the verified URLs for the 6 specific UCI datasets
DATASETS = {
    'wine': {
        'url': 'https://archive.ics.uci.edu/ml/machine-learning-databases/wine/wine.data',
        'name': 'Wine',
        'has_header': False,
        'delimiter': ','
    },
    'abalone': {
        'url': 'https://archive.ics.uci.edu/ml/machine-learning-databases/abalone/abalone.data',
        'name': 'Abalone',
        'has_header': False,
        'delimiter': ','
    },
    'breast_cancer': {
        'url': 'https://archive.ics.uci.edu/ml/machine-learning-databases/breast-cancer-wisconsin/wdbc.data',
        'name': 'Breast Cancer Wisconsin (Diagnostic)',
        'has_header': False,
        'delimiter': ','
    },
    'student_performance': {
        'url': 'https://archive.ics.uci.edu/ml/machine-learning-databases/00295/student-mat.csv',
        'name': 'Student Performance',
        'has_header': True,
        'delimiter': ';'
    },
    'air_quality': {
        'url': 'https://archive.ics.uci.edu/ml/machine-learning-databases/00360/AirQualityUCI.zip',
        'name': 'Air Quality',
        'has_header': True,
        'delimiter': ';',
        'note': 'Requires unzipping and processing specific file inside'
    },
    'concrete': {
        'url': 'https://archive.ics.uci.edu/ml/machine-learning-databases/concrete/compressive/Concrete_Data.xls',
        'name': 'Concrete Compressive Strength',
        'has_header': True,
        'delimiter': ',' # Excel file, handled differently
    }
}

FALLBACK_DATASETS = {
    'parkinsons': {
        'url': 'https://archive.ics.uci.edu/ml/machine-learning-databases/parkinsons/parkinsons.data',
        'name': 'Parkinsons',
        'has_header': True,
        'delimiter': ','
    },
    'libras': {
        'url': 'https://archive.ics.uci.edu/ml/machine-learning-databases/libras/movement_libras.data',
        'name': 'Libras',
        'has_header': False,
        'delimiter': ','
    },
    'isolet': {
        'url': 'https://archive.ics.uci.edu/ml/machine-learning-databases/isolet/isolet_data.txt',
        'name': 'Isolet',
        'has_header': False,
        'delimiter': ' '
    }
}

def fetch_uci_dataset(dataset_key: str, force_download: bool = False) -> str:
    """
    Fetch a dataset from UCI and save to data/raw.
    Returns the path to the downloaded file.
    Raises FileNotFoundError if download fails.
    """
    config = get_config()
    raw_dir = Path(config['paths']['raw'])
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    # Select dataset source
    if dataset_key in DATASETS:
        ds_info = DATASETS[dataset_key]
    elif dataset_key in FALLBACK_DATASETS:
        ds_info = FALLBACK_DATASETS[dataset_key]
    else:
        raise ValueError(f"Unknown dataset key: {dataset_key}")
    
    url = ds_info['url']
    filename = url.split('/')[-1]
    # Handle .zip or .xls by keeping extension, but we might need to rename for CSV processing
    local_path = raw_dir / filename
    
    # Check if already downloaded and valid
    if not force_download and local_path.exists():
        # Verify checksum if we have one
        checksums = load_checksums(str(raw_dir / 'checksums.json'))
        if filename in checksums:
            if verify_checksum(str(local_path), checksums[filename]):
                logger.info(f"Using cached valid file: {filename}")
                return str(local_path)
        else:
            logger.info(f"File exists but no checksum found: {filename}")
    
    logger.info(f"Downloading {ds_info['name']} from {url}")
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        with open(local_path, 'wb') as f:
            f.write(response.content)
        
        # Compute and save checksum
        new_hash = compute_file_hash(str(local_path))
        checksums = load_checksums(str(raw_dir / 'checksums.json'))
        checksums[filename] = new_hash
        save_checksums(checksums, str(raw_dir / 'checksums.json'))
        logger.info(f"Downloaded and checksummed: {filename} ({new_hash[:16]}...)")
        
        return str(local_path)
        
    except requests.RequestException as e:
        logger.error(f"Failed to download {dataset_key}: {e}")
        # Per Constitution VII: Fail loudly, no synthetic fallback
        raise FileNotFoundError(f"Could not download dataset {dataset_key} from {url}: {e}")

def load_dataset_from_path(file_path: str, has_header: bool = False, delimiter: str = ',') -> pd.DataFrame:
    """Load CSV/Text file into DataFrame with basic hygiene."""
    try:
        if file_path.endswith('.xls') or file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        elif file_path.endswith('.zip'):
            # Special handling for zip files if needed, currently assuming raw CSV inside
            # For this implementation, we assume the zip is extracted or handled by fetch logic
            # If fetch returns a zip, we need to unzip. 
            # Simplified: assume fetch_uci_dataset returns a path to a readable CSV/Text file
            # or we unzip here.
            import zipfile
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # Extract to a temp location or raw dir
                extract_path = Path(file_path).parent / (Path(file_path).stem + "_extracted")
                extract_path.mkdir(exist_ok=True)
                zip_ref.extractall(extract_path)
                # Find the first CSV/Text file
                for f in extract_path.iterdir():
                    if f.suffix in ['.csv', '.txt', '.data']:
                        file_path = str(f)
                        break
            return load_dataset_from_path(file_path, has_header, delimiter)
        
        df = pd.read_csv(file_path, delimiter=delimiter, header=0 if has_header else None)
        return df
    except Exception as e:
        logger.error(f"Failed to load dataset from {file_path}: {e}")
        raise

# --- Data Hygiene (T006 Implementation) ---

def drop_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows with any missing values."""
    initial_len = len(df)
    df_clean = df.dropna()
    dropped = initial_len - len(df_clean)
    if dropped > 0:
        logger.info(f"Dropped {dropped} rows with missing values.")
    return df_clean

def detect_constant_variables(df: pd.DataFrame) -> List[str]:
    """Identify columns with constant values (variance == 0)."""
    constant_cols = []
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            if df[col].var() == 0:
                constant_cols.append(col)
        else:
            # For non-numeric, check unique count
            if df[col].nunique() == 1:
                constant_cols.append(col)
    return constant_cols

def exclude_constant_variables(df: pd.DataFrame, constant_cols: List[str]) -> pd.DataFrame:
    """Drop constant columns."""
    if constant_cols:
        logger.info(f"Excluding constant variables: {constant_cols}")
        return df.drop(columns=constant_cols)
    return df

def filter_continuous_variables(df: pd.DataFrame, min_count: int = 20) -> pd.DataFrame:
    """Keep only numeric columns suitable for correlation."""
    numeric_df = df.select_dtypes(include=[np.number])
    if len(numeric_df.columns) < min_count:
        logger.warning(f"Dataset has only {len(numeric_df.columns)} numeric columns, filtering might be too aggressive.")
    return numeric_df

def validate_dataset_dimensions(df: pd.DataFrame, min_rows: int = 20, min_cols: int = 3):
    """Ensure dataset is large enough for analysis."""
    if len(df) < min_rows:
        raise ValueError(f"Dataset has only {len(df)} rows, minimum is {min_rows}.")
    if len(df.columns) < min_cols:
        raise ValueError(f"Dataset has only {len(df.columns)} columns, minimum is {min_cols}.")

def apply_hygiene_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    """Apply all hygiene steps."""
    df = drop_missing_values(df)
    constant_cols = detect_constant_variables(df)
    df = exclude_constant_variables(df, constant_cols)
    df = filter_continuous_variables(df)
    validate_dataset_dimensions(df)
    return df

def load_and_hygiene_dataset(dataset_key: str) -> pd.DataFrame:
    """Full pipeline: fetch, load, hygiene."""
    file_path = fetch_uci_dataset(dataset_key)
    ds_info = DATASETS.get(dataset_key, FALLBACK_DATASETS.get(dataset_key))
    df = load_dataset_from_path(file_path, ds_info['has_header'], ds_info['delimiter'])
    df = apply_hygiene_pipeline(df)
    logger.info(f"Loaded and cleaned dataset {dataset_key}: {df.shape}")
    return df

def main():
    """CLI entry point for loaders."""
    import argparse
    parser = argparse.ArgumentParser(description='Load and process UCI datasets.')
    parser.add_argument('--output', type=str, default='data/processed/', help='Output directory for processed data.')
    parser.add_argument('--datasets', type=str, nargs='+', default=list(DATASETS.keys()), help='Dataset keys to load.')
    args = parser.parse_args()
    
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for key in args.datasets:
        try:
            df = load_and_hygiene_dataset(key)
            out_file = output_dir / f"{key}_cleaned.csv"
            df.to_csv(out_file, index=False)
            logger.info(f"Saved processed data to {out_file}")
        except Exception as e:
            logger.error(f"Failed to process dataset {key}: {e}")
            # Continue with next dataset, but the script exit code will be handled by caller if needed

if __name__ == '__main__':
    main()
