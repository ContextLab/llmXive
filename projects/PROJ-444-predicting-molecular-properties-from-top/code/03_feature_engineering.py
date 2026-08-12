"""
Feature Engineering Module for Molecular Property Prediction.

This module merges traditional molecular descriptors with topological data analysis (TDA)
features to create a unified feature matrix for downstream model training.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Tuple, Optional

import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/logs/feature_engineering.log')
    ]
)
logger = logging.getLogger(__name__)

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / 'data' / 'processed'
DATA_LOGS_DIR = PROJECT_ROOT / 'data' / 'logs'

# Ensure log directory exists
DATA_LOGS_DIR.mkdir(parents=True, exist_ok=True)

def load_traditional_descriptors() -> pd.DataFrame:
    """
    Load traditional molecular descriptors from CSV.

    Returns:
        pd.DataFrame: DataFrame containing traditional descriptors.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If required columns are missing.
    """
    file_path = DATA_PROCESSED_DIR / 'traditional_descriptors.csv'
    
    if not file_path.exists():
        raise FileNotFoundError(
            f"Traditional descriptors file not found at {file_path}. "
            "Please run 02_tda_computation.py first."
        )
    
    logger.info(f"Loading traditional descriptors from {file_path}")
    df = pd.read_csv(file_path)
    
    # Validate minimal schema
    required_cols = ['smiles', 'logP']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in traditional descriptors: {missing}")
    
    logger.info(f"Loaded {len(df)} rows with {len(df.columns)} columns")
    return df

def load_tda_features() -> pd.DataFrame:
    """
    Load TDA features from CSV.

    Returns:
        pd.DataFrame: DataFrame containing TDA features.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If required columns are missing.
    """
    file_path = DATA_PROCESSED_DIR / 'tda_features.csv'
    
    if not file_path.exists():
        raise FileNotFoundError(
            f"TDA features file not found at {file_path}. "
            "Please run 02_tda_computation.py first."
        )
    
    logger.info(f"Loading TDA features from {file_path}")
    df = pd.read_csv(file_path)
    
    # Validate minimal schema
    if 'smiles' not in df.columns:
        raise ValueError("Missing 'smiles' column in TDA features")
    
    logger.info(f"Loaded {len(df)} rows with {len(df.columns)} columns")
    return df

def merge_features(
    traditional_df: pd.DataFrame,
    tda_df: pd.DataFrame,
    on: str = 'smiles'
) -> pd.DataFrame:
    """
    Merge traditional descriptors and TDA features on the specified key.

    Args:
        traditional_df: DataFrame with traditional descriptors.
        tda_df: DataFrame with TDA features.
        on: Column name to join on (default: 'smiles').

    Returns:
        pd.DataFrame: Merged DataFrame.

    Raises:
        ValueError: If merge results in zero rows or significant data loss.
    """
    logger.info(f"Merging datasets on column '{on}'")
    
    # Perform inner join to ensure consistency
    merged = pd.merge(
        traditional_df,
        tda_df,
        on=on,
        how='inner',
        suffixes=('_trad', '_tda')
    )
    
    if len(merged) == 0:
        raise ValueError("Merge resulted in zero rows. Check for mismatched SMILES.")
    
    # Log data loss if any
    expected_len = min(len(traditional_df), len(tda_df))
    if len(merged) < expected_len:
        logger.warning(
            f"Data loss detected during merge. "
            f"Expected at least {expected_len} rows, got {len(merged)}."
        )
    
    logger.info(f"Merged dataset has {len(merged)} rows and {len(merged.columns)} columns")
    return merged

def prepare_combined_feature_matrix(
    merged_df: pd.DataFrame,
    target_col: str = 'logP',
    exclude_cols: Optional[list] = None
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Prepare the final feature matrix (X) and target vector (y).

    Args:
        merged_df: The merged DataFrame.
        target_col: Name of the target column (default: 'logP').
        exclude_cols: List of columns to exclude from features (e.g., identifiers).

    Returns:
        Tuple[pd.DataFrame, pd.Series]: Feature matrix and target vector.
    """
    if exclude_cols is None:
        exclude_cols = ['smiles']
    
    if target_col not in merged_df.columns:
        raise ValueError(f"Target column '{target_col}' not found in merged data")
    
    # Separate features and target
    X = merged_df.drop(columns=[target_col] + exclude_cols, errors='ignore')
    y = merged_df[target_col]
    
    # Handle non-numeric columns if any (drop or encode)
    numeric_cols = X.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) < len(X.columns):
        non_numeric = [c for c in X.columns if c not in numeric_cols]
        logger.warning(f"Dropping non-numeric columns: {non_numeric}")
        X = X[numeric_cols]
    
    # Check for NaN values
    if X.isnull().any().any():
        logger.warning("NaN values detected in feature matrix. Filling with 0.")
        X = X.fillna(0)
    
    if y.isnull().any():
        logger.warning("NaN values detected in target vector. Dropping those rows.")
        valid_mask = ~y.isnull()
        X = X[valid_mask]
        y = y[valid_mask]
    
    logger.info(f"Final feature matrix shape: {X.shape}")
    logger.info(f"Final target vector shape: {y.shape}")
    
    return X, y

def save_combined_features(
    merged_df: pd.DataFrame,
    output_path: Optional[Path] = None
) -> Path:
    """
    Save the merged feature set to a CSV file.

    Args:
        merged_df: The merged DataFrame.
        output_path: Optional custom output path.

    Returns:
        Path: Path to the saved file.
    """
    if output_path is None:
        output_path = DATA_PROCESSED_DIR / 'combined_features.csv'
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged_df.to_csv(output_path, index=False)
    logger.info(f"Saved combined features to {output_path}")
    return output_path

def run_feature_engineering() -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    """
    Main entry point to execute the feature engineering pipeline.

    Returns:
        Tuple containing:
            - merged_df: The full merged DataFrame.
            - X: Feature matrix.
            - y: Target vector.
    """
    logger.info("Starting Feature Engineering Pipeline")
    
    # 1. Load data
    trad_df = load_traditional_descriptors()
    tda_df = load_tda_features()
    
    # 2. Merge
    merged_df = merge_features(trad_df, tda_df)
    
    # 3. Prepare matrices
    X, y = prepare_combined_feature_matrix(merged_df)
    
    # 4. Save
    save_combined_features(merged_df)
    
    logger.info("Feature Engineering Pipeline Completed Successfully")
    return merged_df, X, y

def main():
    """CLI entry point."""
    try:
        merged_df, X, y = run_feature_engineering()
        print(f"Success. Merged {len(merged_df)} samples. Features: {X.shape[1]}, Target: {y.shape[0]}")
    except Exception as e:
        logger.error(f"Feature engineering failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()