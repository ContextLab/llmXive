import os
import json
import hashlib
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
from ucimlrepo import fetch_dataset

def ensure_data_raw_dir() -> str:
    """Ensure the data/raw directory exists."""
    path = "data/raw"
    os.makedirs(path, exist_ok=True)
    return path

def compute_file_checksum(filepath: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_breast_cancer_dataset() -> Tuple[pd.DataFrame, str]:
    """
    Download UCI Breast Cancer (Wisconsin Diagnostic) dataset.
    Dataset ID: 197
    """
    print("Downloading UCI Breast Cancer dataset (ID: 197)...")
    dataset = fetch_dataset(197)
    df = dataset.data.features
    return df, "breast_cancer"

def download_wine_dataset() -> Tuple[pd.DataFrame, str]:
    """
    Download UCI Wine dataset.
    Dataset ID: 198
    """
    print("Downloading UCI Wine dataset (ID: 198)...")
    dataset = fetch_dataset(198)
    df = dataset.data.features
    return df, "wine"

def download_adult_dataset() -> Tuple[pd.DataFrame, str]:
    """
    Download UCI Adult (Census Income) dataset.
    Dataset ID: 522
    """
    print("Downloading UCI Adult dataset (ID: 522)...")
    dataset = fetch_dataset(522)
    df = dataset.data.features
    return df, "adult"

def prepare_data_for_ttest(df: pd.DataFrame, target_column: str, group_column: str = None) -> Tuple[np.ndarray, np.ndarray]:
    """Prepare data for t-test from a DataFrame."""
    if group_column:
        groups = df[group_column].unique()
        if len(groups) < 2:
            raise ValueError("Need at least 2 groups for t-test")
        
        group1 = df[df[group_column] == groups[0]][target_column].dropna()
        group2 = df[df[group_column] == groups[1]][target_column].dropna()
        
        return group1.values, group2.values
    else:
        # Use median split if no group column provided
        median = df[target_column].median()
        below = df[df[target_column] < median][target_column].dropna()
        above = df[df[target_column] >= median][target_column].dropna()
        return below.values, above.values

def prepare_data_for_anova(df: pd.DataFrame, target_column: str, group_column: str) -> List[np.ndarray]:
    """Prepare data for ANOVA from a DataFrame."""
    groups = df[group_column].unique()
    if len(groups) < 2:
        raise ValueError("Need at least 2 groups for ANOVA")
    
    return [df[df[group_column] == g][target_column].dropna().values for g in groups]

def prepare_data_for_chi_squared(df: pd.DataFrame, col1: str, col2: str) -> np.ndarray:
    """Prepare contingency table for chi-squared test."""
    contingency = pd.crosstab(df[col1], df[col2])
    return contingency.values

def preprocess_dataset_for_validation(df: pd.DataFrame, dataset_name: str) -> Dict[str, Any]:
    """Preprocess dataset for validation tests."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    return {
        'dataset_name': dataset_name,
        'n_samples': len(df),
        'n_features': len(df.columns),
        'numeric_columns': numeric_cols,
        'categorical_columns': categorical_cols,
        'missing_values': df.isnull().sum().to_dict()
    }

def main():
    """Main function for dataset validation (T029-T031)."""
    print("Starting dataset validation...")
    
    # Download datasets
    datasets = [
        download_breast_cancer_dataset(),
        download_wine_dataset(),
        download_adult_dataset()
    ]
    
    # Save and verify checksums
    data_dir = ensure_data_raw_dir()
    metadata = {'datasets': []}
    
    for df, name in datasets:
        filepath = os.path.join(data_dir, f"{name}.csv")
        df.to_csv(filepath, index=False)
        
        checksum = compute_file_checksum(filepath)
        metadata['datasets'].append({
            'name': name,
            'filepath': filepath,
            'checksum': checksum,
            'n_samples': len(df)
        })
        
        print(f"Saved {name} dataset: {len(df)} samples, checksum: {checksum[:16]}...")
    
    # Save metadata
    with open("data/simulation_metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print("Dataset validation complete.")

if __name__ == "__main__":
    main()
