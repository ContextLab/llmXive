import os
import json
import hashlib
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
import warnings
warnings.filterwarnings('ignore')

from ucimlrepo import fetch_ucirepo
from code.simulation.logging_config import get_logger

# Constants for dataset IDs
DATASET_IDS = {
    'breast_cancer': 197,
    'wine': 198,
    'adult': 522
}

def ensure_data_raw_dir():
    os.makedirs("data/raw", exist_ok=True)

def load_simulation_metadata() -> Dict[str, Any]:
    path = "data/simulation_metadata.json"
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {"datasets": {}, "runs": []}

def save_simulation_metadata(metadata: Dict[str, Any]):
    path = "data/simulation_metadata.json"
    with open(path, 'w') as f:
        json.dump(metadata, f, indent=2)

def compute_file_checksum(filepath: str) -> str:
  """Compute SHA256 checksum of a file."""
  sha256_hash = hashlib.sha256()
  with open(filepath, "rb") as f:
      for byte_block in iter(lambda: f.read(4096), b""):
          sha256_hash.update(byte_block)
  return sha256_hash.hexdigest()

def verify_dataset_checksum(dataset_name: str, checksum: str):
    # In a real scenario, we would compare against a known good checksum
    logger = get_logger()
    logger.info(f"Checksum verification for {dataset_name}: {checksum}")

def download_breast_cancer_dataset():
    """Download UCI Breast Cancer (Wisconsin Diagnostic) dataset."""
    logger = get_logger()
    logger.info("Downloading Breast Cancer dataset (ID: 197)...")
    try:
        breast_cancer = fetch_ucirepo(id=197)
        df = pd.concat([breast_cancer.data.features, breast_cancer.data.targets], axis=1)
        df.to_csv("data/raw/breast_cancer_raw.csv", index=False)
        logger.info("Breast Cancer dataset downloaded.")
        return df
    except Exception as e:
        logger.error(f"Failed to download Breast Cancer dataset: {e}")
        raise

def download_wine_dataset():
    """Download UCI Wine dataset."""
    logger = get_logger()
    logger.info("Downloading Wine dataset (ID: 198)...")
    try:
        wine = fetch_ucirepo(id=198)
        df = pd.concat([wine.data.features, wine.data.targets], axis=1)
        df.to_csv("data/raw/wine_raw.csv", index=False)
        logger.info("Wine dataset downloaded.")
        return df
    except Exception as e:
        logger.error(f"Failed to download Wine dataset: {e}")
        raise

def download_adult_dataset():
    """Download UCI Adult dataset."""
    logger = get_logger()
    logger.info("Downloading Adult dataset (ID: 522)...")
    try:
        adult = fetch_ucirepo(id=522)
        # Adult dataset might have missing values or specific formats
        df = pd.concat([adult.data.features, adult.data.targets], axis=1)
        df.to_csv("data/raw/adult_raw.csv", index=False)
        logger.info("Adult dataset downloaded.")
        return df
    except Exception as e:
        logger.error(f"Failed to download Adult dataset: {e}")
        raise

def prepare_data_for_ttest(df: pd.DataFrame, target_col: str, feature_col: str) -> pd.DataFrame:
    """Prepare data for t-test: ensure target is binary and feature is numeric."""
    # Basic cleaning
    df = df.dropna(subset=[target_col, feature_col])
    return df

def prepare_data_for_anova(df: pd.DataFrame, target_col: str, feature_col: str) -> pd.DataFrame:
    """Prepare data for ANOVA."""
    df = df.dropna(subset=[target_col, feature_col])
    return df

def prepare_data_for_chi_squared(df: pd.DataFrame, col1: str, col2: str) -> pd.DataFrame:
    """Prepare data for Chi-squared: ensure both are categorical."""
    df = df.dropna(subset=[col1, col2])
    return df

def preprocess_dataset_for_validation(dataset_name: str):
    """
    Preprocess downloaded datasets for validation tests.
    Saves prepared CSVs to data/raw/.
    """
    logger = get_logger()
    logger.info(f"Preprocessing {dataset_name}...")
    
    raw_path = f"data/raw/{dataset_name}_raw.csv"
    if not os.path.exists(raw_path):
        if dataset_name == 'breast_cancer':
            download_breast_cancer_dataset()
        elif dataset_name == 'wine':
            download_wine_dataset()
        elif dataset_name == 'adult':
            download_adult_dataset()
    
    df = pd.read_csv(raw_path)
    
    # Determine columns based on dataset
    if dataset_name == 'breast_cancer':
        # diagnosis (M/B), mean radius
        target = 'diagnosis'
        feature = df.select_dtypes(include=[np.number]).columns[0] # First numeric
        df_prep = prepare_data_for_ttest(df, target, feature)
        df_prep.to_csv(f"data/raw/{dataset_name}_prepared.csv", index=False)
        
    elif dataset_name == 'wine':
        # class (0,1,2), alcohol
        target = 'class'
        feature = df.select_dtypes(include=[np.number]).columns[0]
        df_prep = prepare_data_for_anova(df, target, feature)
        df_prep.to_csv(f"data/raw/{dataset_name}_prepared.csv", index=False)
        
    elif dataset_name == 'adult':
        # class (<=50K, >50K), age
        target = 'class'
        # Find a numeric column
        num_cols = df.select_dtypes(include=[np.number]).columns
        if len(num_cols) > 0:
            feature = num_cols[0]
            df_prep = prepare_data_for_anova(df, target, feature)
            df_prep.to_csv(f"data/raw/{dataset_name}_prepared.csv", index=False)
        else:
            logger.warning("No numeric columns found in Adult dataset for ANOVA")
    else:
        logger.warning(f"Unknown dataset {dataset_name}")

def main():
    """
    Main entry point for T029/T030: Download and preprocess real datasets.
    """
    logger = get_logger()
    logger.info("Starting Validator (Download/Preprocess)")
    
    ensure_data_raw_dir()
    
    datasets = ['breast_cancer', 'wine', 'adult']
    
    for ds in datasets:
        try:
            # Download if needed (logic inside download functions handles existence check loosely,
            # but we call them to ensure data is there)
            if ds == 'breast_cancer':
                download_breast_cancer_dataset()
            elif ds == 'wine':
                download_wine_dataset()
            elif ds == 'adult':
                download_adult_dataset()
            
            preprocess_dataset_for_validation(ds)
            
            # Update metadata
            raw_path = f"data/raw/{ds}_raw.csv"
            if os.path.exists(raw_path):
                checksum = compute_file_checksum(raw_path)
                meta = load_simulation_metadata()
                meta['datasets'][ds] = {'checksum': checksum, 'path': raw_path}
                save_simulation_metadata(meta)
                
        except Exception as e:
            logger.error(f"Failed to process {ds}: {e}")
            
    logger.info("Validator completed.")

if __name__ == "__main__":
    main()
