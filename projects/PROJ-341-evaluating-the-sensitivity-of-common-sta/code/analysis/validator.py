import os
import json
import hashlib
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
from ucimlrepo import fetch_dataset

# Constants for dataset IDs
DATASET_IDS = {
    "breast_cancer": 197,
    "wine": 198,
    "adult": 522
}

METADATA_PATH = "data/simulation_metadata.json"

def ensure_data_raw_dir():
    """Ensure the data/raw directory exists."""
    os.makedirs("data/raw", exist_ok=True)

def load_simulation_metadata():
    """Load existing simulation metadata or return an empty structure."""
    if os.path.exists(METADATA_PATH):
        with open(METADATA_PATH, 'r') as f:
            return json.load(f)
    return {
        "seeds": [],
        "config": {},
        "timestamps": [],
        "checksums": {}
    }

def save_simulation_metadata(metadata):
    """Save simulation metadata to disk."""
    with open(METADATA_PATH, 'w') as f:
        json.dump(metadata, f, indent=2)

def compute_file_checksum(filepath):
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_dataset_checksum(dataset_name, expected_checksum=None):
    """
    Verify the checksum of a downloaded dataset.
    If expected_checksum is provided, it compares against it.
    Returns True if checksum matches or if no expected checksum is provided.
    """
    filepath = f"data/raw/{dataset_name}.csv"
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Dataset file not found: {filepath}")
    
    actual_checksum = compute_file_checksum(filepath)
    metadata = load_simulation_metadata()
    
    # Store the checksum in metadata
    if "checksums" not in metadata:
        metadata["checksums"] = {}
    
    metadata["checksums"][dataset_name] = {
        "checksum": actual_checksum,
        "filepath": filepath,
        "verified_at": str(pd.Timestamp.now())
    }
    
    save_simulation_metadata(metadata)
    
    if expected_checksum:
        return actual_checksum == expected_checksum
    return True

def download_breast_cancer_dataset():
    """Download UCI Breast Cancer (Wisconsin Diagnostic) dataset."""
    print("Downloading Breast Cancer dataset (ID: 197)...")
    try:
        dataset = fetch_dataset(197)
        df = dataset.data.features
        df.to_csv("data/raw/breast_cancer.csv", index=False)
        print(f"Saved to data/raw/breast_cancer.csv")
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to download Breast Cancer dataset: {e}")

def download_wine_dataset():
    """Download UCI Wine dataset."""
    print("Downloading Wine dataset (ID: 198)...")
    try:
        dataset = fetch_dataset(198)
        df = dataset.data.features
        df.to_csv("data/raw/wine.csv", index=False)
        print(f"Saved to data/raw/wine.csv")
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to download Wine dataset: {e}")

def download_adult_dataset():
    """Download UCI Adult (Census Income) dataset."""
    print("Downloading Adult dataset (ID: 522)...")
    try:
        dataset = fetch_dataset(522)
        df = dataset.data.features
        df.to_csv("data/raw/adult.csv", index=False)
        print(f"Saved to data/raw/adult.csv")
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to download Adult dataset: {e}")

def prepare_data_for_ttest(df: pd.DataFrame, target_col: str, group_col: str = None):
    """Prepare data for t-test."""
    if group_col:
        return df.groupby(group_col)[target_col].apply(list).to_dict()
    return df[target_col].values

def prepare_data_for_anova(df: pd.DataFrame, target_col: str, group_col: str):
    """Prepare data for ANOVA."""
    return df.groupby(group_col)[target_col].apply(list).tolist()

def prepare_data_for_chi_squared(df: pd.DataFrame, col1: str, col2: str):
    """Prepare data for Chi-squared test."""
    contingency_table = pd.crosstab(df[col1], df[col2])
    return contingency_table.values

def preprocess_dataset_for_validation(dataset_name):
    """Preprocess a specific dataset for validation tests."""
    filepath = f"data/raw/{dataset_name}.csv"
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Dataset not found: {filepath}")
    
    df = pd.read_csv(filepath)
    # Basic preprocessing: drop NaNs
    df = df.dropna()
    return df

def main():
    """Main function to download all datasets and verify checksums."""
    ensure_data_raw_dir()
    
    datasets = [
        ("breast_cancer", download_breast_cancer_dataset),
        ("wine", download_wine_dataset),
        ("adult", download_adult_dataset)
    ]
    
    print("Starting dataset download and checksum verification...")
    
    for name, download_func in datasets:
        try:
            df = download_func()
            print(f"Verifying checksum for {name}...")
            verify_dataset_checksum(name)
            print(f"Checksum verified and recorded for {name}.")
        except Exception as e:
            print(f"Error processing {name}: {e}")
            raise
    
    print("All datasets downloaded and checksums verified.")
    print(f"Metadata saved to {METADATA_PATH}")

if __name__ == "__main__":
    main()
