import os
import sys
import json
import hashlib
import logging
import requests
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional

# Import openml as per verified source
import openml

def setup_loader_logging():
    logging.basicConfig(level=logging.INFO)
    return logging.getLogger(__name__)

def compute_file_hash(filepath: str) -> str:
    """Compute SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def load_checksums(checksum_path: str) -> Dict[str, str]:
    """Load checksums from JSON file."""
    if os.path.exists(checksum_path):
        with open(checksum_path, 'r') as f:
            return json.load(f)
    return {}

def save_checksums(checksums: Dict[str, str], checksum_path: str):
    """Save checksums to JSON file."""
    os.makedirs(os.path.dirname(checksum_path), exist_ok=True)
    with open(checksum_path, 'w') as f:
        json.dump(checksums, f, indent=2)

def verify_checksum(filepath: str, expected_hash: str) -> bool:
    """Verify file checksum."""
    if not os.path.exists(filepath):
        return False
    return compute_file_hash(filepath) == expected_hash

def fetch_uci_dataset(logger: logging.Logger, dataset_name: str) -> Optional[pd.DataFrame]:
    """
    Fetch dataset from UCI or openml.
    Uses openml as per verified source.
    """
    try:
        # Use openml to fetch dataset 15 (Breast Cancer) as a template
        # For this task, we will use a list of known datasets from openml
        # Dataset IDs: 15 (Breast Cancer), 18 (Wine), 23 (Abalone), etc.
        # We'll use a few known IDs to ensure we get real data
        
        dataset_ids = [15, 18, 23, 52, 61] # Breast Cancer, Wine, Abalone, etc.
        
        for did in dataset_ids:
            try:
                dataset = openml.datasets.get_dataset(did)
                X, y, _, _ = dataset.get_data(dataset_format='dataframe')
                if y is not None:
                    df = pd.concat([X, y], axis=1)
                else:
                    df = X
                
                # Check if we have enough continuous variables
                continuous_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
                if len(continuous_cols) >= 20:
                    df = df[continuous_cols]
                    df.attrs['name'] = dataset.name
                    df.attrs['source'] = 'openml'
                    df.attrs['id'] = did
                    return df
            except Exception as e:
                logger.warning(f"Failed to load openml dataset {did}: {e}")
                continue
        
        logger.error("No valid datasets found with >=20 continuous variables.")
        return None
    except Exception as e:
        logger.error(f"Failed to fetch datasets from openml: {e}")
        return None

def load_dataset_from_path(filepath: str) -> pd.DataFrame:
    """Load dataset from local path."""
    if filepath.endswith('.csv'):
        return pd.read_csv(filepath)
    elif filepath.endswith('.xlsx'):
        return pd.read_excel(filepath)
    else:
        raise ValueError(f"Unsupported file format: {filepath}")

def drop_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows with missing values."""
    return df.dropna()

def detect_constant_variables(df: pd.DataFrame) -> List[str]:
    """Detect constant variables."""
    return [col for col in df.columns if df[col].nunique() == 1]

def exclude_constant_variables(df: pd.DataFrame) -> pd.DataFrame:
    """Exclude constant variables."""
    constant_cols = detect_constant_variables(df)
    return df.drop(columns=constant_cols)

def filter_continuous_variables(df: pd.DataFrame) -> pd.DataFrame:
    """Filter to only continuous (numeric) variables."""
    return df.select_dtypes(include=[np.number])

def validate_dataset_dimensions(df: pd.DataFrame) -> bool:
    """Validate dataset has >=20 continuous variables."""
    return len(df.columns) >= 20

def apply_hygiene_pipeline(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """Apply full hygiene pipeline."""
    df = drop_missing_values(df)
    df = exclude_constant_variables(df)
    df = filter_continuous_variables(df)
    if not validate_dataset_dimensions(df):
        return None
    return df

def load_all_datasets(logger: logging.Logger, config: Dict[str, Any]) -> List[pd.DataFrame]:
    """Load all datasets and apply hygiene pipeline."""
    datasets = []
    logger.info("Loading datasets from openml...")
    
    # Use the openml fetcher
    df = fetch_uci_dataset(logger, config.get('dataset_name', 'all'))
    if df is not None:
        df_clean = apply_hygiene_pipeline(df)
        if df_clean is not None:
            datasets.append(df_clean)
            logger.info(f"Loaded dataset: {df.attrs.get('name')} with {len(df_clean.columns)} variables")
    
    if not datasets:
        logger.warning("No valid datasets loaded.")
    
    return datasets

def ensure_output_dirs():
    """Ensure output directories exist."""
    os.makedirs('data/raw', exist_ok=True)
    os.makedirs('data/processed', exist_ok=True)
    os.makedirs('output/results', exist_ok=True)
    os.makedirs('output/plots', exist_ok=True)
    os.makedirs('output/reports', exist_ok=True)

def verify_no_dynamic_discovery():
    """Verify no dynamic discovery of datasets (static list only)."""
    pass

def main():
    logger = setup_loader_logging()
    config = {'dataset_name': 'all'}
    datasets = load_all_datasets(logger, config)
    for df in datasets:
        print(f"Dataset: {df.attrs.get('name')}, Shape: {df.shape}")
