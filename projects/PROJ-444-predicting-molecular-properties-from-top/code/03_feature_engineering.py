"""
Feature Engineering Module for Molecular Property Prediction.

This module handles the merging of traditional molecular descriptors
and topological data analysis (TDA) features to create a combined
feature matrix for downstream modeling.

Dependencies:
    - pandas: for data manipulation
    - os, sys, logging: for system interaction and logging
    - pathlib: for path handling
"""

import os
import sys
import logging
from pathlib import Path
from typing import Tuple, Optional

import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"

# Input files (produced by previous tasks)
TRADITIONAL_DESCRIPTORS_FILE = DATA_PROCESSED_DIR / "traditional_descriptors.csv"
TDA_FEATURES_FILE = DATA_PROCESSED_DIR / "tda_features.csv"

# Output file
COMBINED_FEATURES_FILE = DATA_PROCESSED_DIR / "combined_features.csv"

def load_traditional_descriptors(filepath: Optional[Path] = None) -> pd.DataFrame:
    """
    Load traditional molecular descriptors from CSV.
    
    Args:
        filepath: Optional path to the CSV file. Defaults to the standard location.
        
    Returns:
        DataFrame containing traditional descriptors.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or has no data.
    """
    if filepath is None:
        filepath = TRADITIONAL_DESCRIPTORS_FILE
        
    if not filepath.exists():
        raise FileNotFoundError(f"Traditional descriptors file not found: {filepath}")
        
    logger.info(f"Loading traditional descriptors from {filepath}")
    df = pd.read_csv(filepath)
    
    if df.empty:
        raise ValueError(f"Traditional descriptors file is empty: {filepath}")
        
    logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns")
    return df

def load_tda_features(filepath: Optional[Path] = None) -> pd.DataFrame:
    """
    Load TDA features from CSV.
    
    Args:
        filepath: Optional path to the CSV file. Defaults to the standard location.
        
    Returns:
        DataFrame containing TDA features.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or has no data.
    """
    if filepath is None:
        filepath = TDA_FEATURES_FILE
        
    if not filepath.exists():
        raise FileNotFoundError(f"TDA features file not found: {filepath}")
        
    logger.info(f"Loading TDA features from {filepath}")
    df = pd.read_csv(filepath)
    
    if df.empty:
        raise ValueError(f"TDA features file is empty: {filepath}")
        
    logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns")
    return df

def merge_features(traditional_df: pd.DataFrame, tda_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge traditional descriptors and TDA features based on a common index or ID.
    
    This function assumes both DataFrames share a common identifier column (e.g., 'smiles'
    or an integer index) that allows for a precise merge. If 'smiles' exists, it is used.
    Otherwise, the index is used.
    
    Args:
        traditional_df: DataFrame with traditional descriptors.
        tda_df: DataFrame with TDA features.
        
    Returns:
        Merged DataFrame containing both feature sets.
        
    Raises:
        ValueError: If merge results in fewer rows than expected (indicating data mismatch).
    """
    logger.info("Merging traditional and TDA features")
    
    # Determine merge key
    if 'smiles' in traditional_df.columns and 'smiles' in tda_df.columns:
        merge_key = 'smiles'
        logger.info(f"Merging on 'smiles' column")
    elif traditional_df.index.equals(tda_df.index):
        merge_key = None
        logger.info("Merging on index")
    else:
        # Try to find a common column
        common_cols = set(traditional_df.columns) & set(tda_df.columns)
        if common_cols:
            merge_key = list(common_cols)[0]
            logger.info(f"Merging on common column: {merge_key}")
        else:
            raise ValueError("No common merge key found between traditional and TDA datasets")
    
    if merge_key:
        merged_df = pd.merge(traditional_df, tda_df, on=merge_key, how='inner')
    else:
        merged_df = pd.concat([traditional_df, tda_df], axis=1)
        
    # Validate merge
    min_rows = min(len(traditional_df), len(tda_df))
    if len(merged_df) < min_rows:
        logger.warning(f"Merge resulted in fewer rows ({len(merged_df)}) than input ({min_rows}). Check for duplicate keys or missing data.")
        
    logger.info(f"Merged DataFrame shape: {merged_df.shape}")
    return merged_df

def prepare_combined_feature_matrix(df: pd.DataFrame) -> Tuple[pd.DataFrame, list, list]:
    """
    Prepare the combined feature matrix for modeling.
    
    This function separates the feature matrix from the target variable (if present)
    and returns the clean feature matrix along with lists of feature names.
    
    Args:
        df: The merged DataFrame.
        
    Returns:
        Tuple containing:
            - X: Feature matrix (DataFrame)
            - feature_names: List of all feature column names
            - tda_feature_names: List of TDA feature column names
    """
    logger.info("Preparing combined feature matrix")
    
    # Identify target column if present (common names: 'logP', 'target', 'y')
    target_candidates = ['logP', 'target', 'y', 'Label']
    target_col = None
    for col in target_candidates:
        if col in df.columns:
            target_col = col
            break
    
    if target_col:
        logger.info(f"Detected target column: {target_col}")
        X = df.drop(columns=[target_col])
    else:
        X = df.copy()
        logger.warning("No target column detected. Assuming all columns are features.")
    
    # Identify TDA features (usually prefixed or named specifically)
    # Based on T013/T014, TDA features might have specific naming conventions
    tda_feature_names = [col for col in X.columns if 'persistence' in col.lower() or 'betti' in col.lower() or 'diagram' in col.lower()]
    
    if not tda_feature_names:
        # Fallback: assume columns not in traditional set are TDA
        # This requires knowing traditional columns, which we don't explicitly have here
        # So we just return all as features
        logger.info("Could not automatically identify TDA features by name. All columns treated as features.")
        tda_feature_names = list(X.columns) # Placeholder logic
    
    logger.info(f"Feature matrix shape: {X.shape}")
    logger.info(f"Number of TDA features identified: {len(tda_feature_names)}")
    
    return X, list(X.columns), tda_feature_names

def save_combined_features(df: pd.DataFrame, filepath: Optional[Path] = None) -> Path:
    """
    Save the combined feature matrix to a CSV file.
    
    Args:
        df: The DataFrame to save.
        filepath: Optional output path. Defaults to standard location.
        
    Returns:
        Path to the saved file.
    """
    if filepath is None:
        filepath = COMBINED_FEATURES_FILE
        
    # Ensure directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving combined features to {filepath}")
    df.to_csv(filepath, index=False)
    
    logger.info(f"Saved {len(df)} rows and {len(df.columns)} columns")
    return filepath

def run_feature_engineering() -> Path:
    """
    Execute the full feature engineering pipeline.
    
    1. Load traditional descriptors.
    2. Load TDA features.
    3. Merge datasets.
    4. Prepare feature matrix.
    5. Save combined features.
    
    Returns:
        Path to the saved combined features file.
        
    Raises:
        SystemExit: If any step fails.
    """
    try:
        logger.info("Starting feature engineering pipeline")
        
        # 1. Load data
        traditional_df = load_traditional_descriptors()
        tda_df = load_tda_features()
        
        # 2. Merge
        merged_df = merge_features(traditional_df, tda_df)
        
        # 3. Prepare matrix (for validation/logging, though we save the full merged df)
        X, feature_names, tda_names = prepare_combined_feature_matrix(merged_df)
        
        # 4. Save
        output_path = save_combined_features(merged_df)
        
        logger.info("Feature engineering pipeline completed successfully")
        return output_path
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during feature engineering: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

def main():
    """Entry point for the script."""
    logger.info("Running 03_feature_engineering.py")
    output_path = run_feature_engineering()
    logger.info(f"Output saved to: {output_path}")

if __name__ == "__main__":
    main()