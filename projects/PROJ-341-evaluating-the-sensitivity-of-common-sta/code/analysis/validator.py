import os
import json
import hashlib
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
from ucimlrepo import fetch_ucirepo
from code.simulation.logging_config import get_logger
from code.utils.checksum_utils import register_dataset_checksum

logger = get_logger(__name__)

def ensure_data_raw_dir():
    """Ensure the data/raw directory exists."""
    os.makedirs('data/raw', exist_ok=True)

def compute_file_checksum(filepath: str) -> str:
    """
    Compute SHA-256 checksum of a file.
    
    Args:
        filepath: Path to the file
        
    Returns:
        Hex string of the checksum
    """
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_breast_cancer_dataset() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Download UCI Breast Cancer (Wisconsin Diagnostic) dataset.
    
    Returns:
        Tuple of (features, targets)
    """
    logger.info("Downloading UCI Breast Cancer dataset (ID: 197)...")
    breast_cancer = fetch_ucirepo(id=197)
    
    features = breast_cancer.data.features
    targets = breast_cancer.data.targets
    
    # Save to disk for checksum verification
    ensure_data_raw_dir()
    features_path = 'data/raw/breast_cancer_features.csv'
    targets_path = 'data/raw/breast_cancer_targets.csv'
    
    features.to_csv(features_path, index=False)
    targets.to_csv(targets_path, index=False)
    
    logger.info(f"Saved Breast Cancer features to {features_path}")
    logger.info(f"Saved Breast Cancer targets to {targets_path}")
    
    return features, targets

def download_wine_dataset() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Download UCI Wine dataset.
    
    Returns:
        Tuple of (features, targets)
    """
    logger.info("Downloading UCI Wine dataset (ID: 198)...")
    wine = fetch_ucirepo(id=198)
    
    features = wine.data.features
    targets = wine.data.targets
    
    # Save to disk for checksum verification
    ensure_data_raw_dir()
    features_path = 'data/raw/wine_features.csv'
    targets_path = 'data/raw/wine_targets.csv'
    
    features.to_csv(features_path, index=False)
    targets.to_csv(targets_path, index=False)
    
    logger.info(f"Saved Wine features to {features_path}")
    logger.info(f"Saved Wine targets to {targets_path}")
    
    return features, targets

def download_adult_dataset() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Download UCI Adult (Census Income) dataset.
    
    Returns:
        Tuple of (features, targets)
    """
    logger.info("Downloading UCI Adult dataset (ID: 522)...")
    adult = fetch_ucirepo(id=522)
    
    features = adult.data.features
    targets = adult.data.targets
    
    # Save to disk for checksum verification
    ensure_data_raw_dir()
    features_path = 'data/raw/adult_features.csv'
    targets_path = 'data/raw/adult_targets.csv'
    
    features.to_csv(features_path, index=False)
    targets.to_csv(targets_path, index=False)
    
    logger.info(f"Saved Adult features to {features_path}")
    logger.info(f"Saved Adult targets to {targets_path}")
    
    return features, targets

def prepare_data_for_ttest(features: pd.DataFrame, targets: pd.DataFrame, 
                           target_column: Optional[str] = None, 
                           feature_column: Optional[str] = None) -> Tuple[np.ndarray, np.ndarray]:
    """
    Prepare data for t-test.
    
    Args:
        features: DataFrame with features
        targets: DataFrame with targets
        target_column: Name of target column (if None, uses first column)
        feature_column: Name of feature column to use (if None, uses first column)
        
    Returns:
        Tuple of (group1, group2) arrays
    """
    if target_column is None:
        target_column = targets.columns[0]
    if feature_column is None:
        feature_column = features.columns[0]
    
    target_values = targets[target_column].unique()
    if len(target_values) != 2:
        raise ValueError(f"Expected 2 target classes for t-test, got {len(target_values)}")
    
    group1 = features[features[target_column] == target_values[0]][feature_column].values
    group2 = features[features[target_column] == target_values[1]][feature_column].values
    
    return group1, group2

def prepare_data_for_anova(features: pd.DataFrame, targets: pd.DataFrame, 
                           target_column: Optional[str] = None, 
                           feature_column: Optional[str] = None) -> List[np.ndarray]:
    """
    Prepare data for ANOVA test.
    
    Args:
        features: DataFrame with features
        targets: DataFrame with targets
        target_column: Name of target column (if None, uses first column)
        feature_column: Name of feature column to use (if None, uses first column)
        
    Returns:
        List of arrays, one per group
    """
    if target_column is None:
        target_column = targets.columns[0]
    if feature_column is None:
        feature_column = features.columns[0]
    
    target_values = targets[target_column].unique()
    groups = []
    for val in target_values:
        group_data = features[features[target_column] == val][feature_column].values
        groups.append(group_data)
    
    return groups

def prepare_data_for_chi_squared(features: pd.DataFrame, targets: pd.DataFrame, 
                                 feature_column: Optional[str] = None, 
                                 target_column: Optional[str] = None) -> np.ndarray:
    """
    Prepare data for chi-squared test (creates contingency table).
    
    Args:
        features: DataFrame with features
        targets: DataFrame with targets
        feature_column: Name of feature column to use (if None, uses first column)
        target_column: Name of target column (if None, uses first column)
        
    Returns:
        Contingency table as numpy array
    """
    if target_column is None:
        target_column = targets.columns[0]
    if feature_column is None:
        feature_column = features.columns[0]
    
    # Create contingency table
    contingency = pd.crosstab(features[feature_column], targets[target_column])
    return contingency.values

def preprocess_dataset_for_validation(dataset_name: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Preprocess a dataset for validation.
    
    Args:
        dataset_name: Name of the dataset ('breast_cancer', 'wine', 'adult')
        
    Returns:
        Tuple of (features, targets)
    """
    if dataset_name == 'breast_cancer':
        features, targets = download_breast_cancer_dataset()
    elif dataset_name == 'wine':
        features, targets = download_wine_dataset()
    elif dataset_name == 'adult':
        features, targets = download_adult_dataset()
    else:
        raise ValueError(f"Unknown dataset: {dataset_name}")
    
    # Register checksums
    ensure_data_raw_dir()
    features_path = f'data/raw/{dataset_name}_features.csv'
    targets_path = f'data/raw/{dataset_name}_targets.csv'
    
    features_checksum = compute_file_checksum(features_path)
    targets_checksum = compute_file_checksum(targets_path)
    
    register_dataset_checksum(dataset_name, {
        'features_path': features_path,
        'features_checksum': features_checksum,
        'targets_path': targets_path,
        'targets_checksum': targets_checksum
    })
    
    logger.info(f"Registered checksums for {dataset_name} dataset")
    
    return features, targets

def main():
    """Main function to download and prepare all datasets."""
    try:
        datasets = ['breast_cancer', 'wine', 'adult']
        
        for dataset_name in datasets:
            logger.info(f"Processing {dataset_name} dataset...")
            features, targets = preprocess_dataset_for_validation(dataset_name)
            logger.info(f"{dataset_name}: {len(features)} samples, {len(features.columns)} features")
        
        logger.info("All datasets downloaded and prepared successfully")
        
    except Exception as e:
        logger.error(f"Error processing datasets: {str(e)}")
        raise

if __name__ == '__main__':
    main()
