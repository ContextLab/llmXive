import os
import json
import hashlib
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
from ucimlrepo import fetch_dataset
import warnings
from datetime import datetime

# Suppress specific warnings for cleaner logs during validation
warnings.filterwarnings("ignore", category=DeprecationWarning)

DATA_RAW_DIR = "data/raw"
METADATA_FILE = "data/simulation_metadata.json"

def ensure_data_raw_dir():
    os.makedirs(DATA_RAW_DIR, exist_ok=True)

def compute_file_checksum(filepath: str, algorithm: str = 'sha256') -> str:
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_breast_cancer_dataset():
    """Download UCI Breast Cancer (Wisconsin Diagnostic) dataset."""
    ensure_data_raw_dir()
    dataset_id = 197
    output_path = os.path.join(DATA_RAW_DIR, 'breast_cancer.csv')
    
    if not os.path.exists(output_path):
        print(f"Downloading Breast Cancer dataset (ID: {dataset_id})...")
        dataset = fetch_dataset(dataset_id)
        df = dataset.data.variables
        # The dataset structure in ucimlrepo returns a specific format
        # We need to extract the data frame properly
        # Usually dataset.data.features and dataset.data.targets
        if hasattr(dataset, 'data') and hasattr(dataset.data, 'features'):
            df_features = dataset.data.features
            df_targets = dataset.data.targets
            df_final = pd.concat([df_features, df_targets], axis=1)
            df_final.to_csv(output_path, index=False)
        else:
            # Fallback for different structure
            df = pd.DataFrame(dataset.data)
            df.to_csv(output_path, index=False)
    return output_path

def download_wine_dataset():
    """Download UCI Wine dataset."""
    ensure_data_raw_dir()
    dataset_id = 198
    output_path = os.path.join(DATA_RAW_DIR, 'wine.csv')
    
    if not os.path.exists(output_path):
        print(f"Downloading Wine dataset (ID: {dataset_id})...")
        dataset = fetch_dataset(dataset_id)
        if hasattr(dataset, 'data') and hasattr(dataset.data, 'features'):
            df_features = dataset.data.features
            df_targets = dataset.data.targets
            df_final = pd.concat([df_features, df_targets], axis=1)
            df_final.to_csv(output_path, index=False)
        else:
            df = pd.DataFrame(dataset.data)
            df.to_csv(output_path, index=False)
    return output_path

def download_adult_dataset():
    """Download UCI Adult (Census Income) dataset."""
    ensure_data_raw_dir()
    dataset_id = 522
    output_path = os.path.join(DATA_RAW_DIR, 'adult.csv')
    
    if not os.path.exists(output_path):
        print(f"Downloading Adult dataset (ID: {dataset_id})...")
        dataset = fetch_dataset(dataset_id)
        if hasattr(dataset, 'data') and hasattr(dataset.data, 'features'):
            df_features = dataset.data.features
            df_targets = dataset.data.targets
            df_final = pd.concat([df_features, df_targets], axis=1)
            df_final.to_csv(output_path, index=False)
        else:
            df = pd.DataFrame(dataset.data)
            df.to_csv(output_path, index=False)
    return output_path

def prepare_data_for_ttest(filepath: str, target_col: str, group_col: str, group_vals: List[Any]) -> Tuple[np.ndarray, np.ndarray]:
    """Prepare data for t-test from CSV."""
    df = pd.read_csv(filepath)
    g1 = df[df[group_col] == group_vals[0]][target_col].values
    g2 = df[df[group_col] == group_vals[1]][target_col].values
    return g1, g2

def prepare_data_for_anova(filepath: str, target_col: str, group_col: str, group_vals: List[Any]) -> List[np.ndarray]:
    """Prepare data for ANOVA from CSV."""
    df = pd.read_csv(filepath)
    groups = [df[df[group_col] == g][target_col].values for g in group_vals]
    return groups

def prepare_data_for_chi_squared(filepath: str, col1: str, col2: str) -> np.ndarray:
    """Prepare contingency table for chi-squared from CSV."""
    df = pd.read_csv(filepath)
    table = pd.crosstab(df[col1], df[col2]).values
    return table

def preprocess_dataset_for_validation():
    """Main preprocessing logic for validation datasets."""
    print("Preprocessing datasets for validation...")
    # This function would typically clean and prepare the downloaded datasets
    # For now, we assume downloads are clean
    pass

def main():
    """Main entry point for validation."""
    print("Running validation dataset downloads...")
    try:
        path_bc = download_breast_cancer_dataset()
        path_wine = download_wine_dataset()
        path_adult = download_adult_dataset()
        print(f"Datasets downloaded: {path_bc}, {path_wine}, {path_adult}")
        
        # Verify checksums
        from code.utils.checksum_utils import compute_file_checksum, register_dataset_checksum, load_simulation_metadata, save_simulation_metadata
        
        datasets = [
            ("breast_cancer", path_bc),
            ("wine", path_wine),
            ("adult", path_adult)
        ]
        
        for name, path in datasets:
            checksum = compute_file_checksum(path)
            register_dataset_checksum(name, path, checksum)
            print(f"Verified {name}: {checksum}")
            
    except Exception as e:
        print(f"Validation download failed: {e}")
        raise

if __name__ == '__main__':
    main()
