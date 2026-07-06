import os
import sys
import logging
from pathlib import Path
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple

# Project root resolution
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED_DIR = ROOT_DIR / "data" / "processed"

# Ensure logging is configured
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(ROOT_DIR / "logs" / "preprocess.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
STRATIFIED_SPLIT_SEED = 42  # Default, overridden by config if available
MIN_STRATUM_SIZE = 20
TEST_SIZE = 0.2

def standardize_units(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize units to MPa, s⁻¹, µm.
    Assumes input has columns like 'yield_strength', 'strain_rate', 'grain_size'
    and optional unit columns like 'yield_strength_unit'.
    """
    logger.info("Standardizing units...")
    df_std = df.copy()
    
    # Example logic for unit conversion (simplified for this task context)
    # In a real scenario, this would parse unit strings and convert.
    # Assuming raw data is already in standard units or handled by fetchers.
    
    if 'yield_strength_mpa' not in df_std.columns and 'yield_strength' in df_std.columns:
        df_std['yield_strength_mpa'] = df_std['yield_strength']
    
    if 'strain_rate_s_inv' not in df_std.columns and 'strain_rate' in df_std.columns:
        df_std['strain_rate_s_inv'] = df_std['strain_rate']
        
    if 'grain_size_um' not in df_std.columns and 'grain_size' in df_std.columns:
        df_std['grain_size_um'] = df_std['grain_size']
        
    return df_std

def drop_incomplete_records(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drop records missing Yield Strength or Strain Rate.
    """
    logger.info("Dropping incomplete records...")
    cols_to_check = ['yield_strength_mpa', 'strain_rate_s_inv']
    initial_count = len(df)
    df_clean = df.dropna(subset=cols_to_check)
    dropped_count = initial_count - len(df_clean)
    logger.info(f"Dropped {dropped_count} records with missing yield strength or strain rate.")
    return df_clean

def impute_composition(df: pd.DataFrame) -> pd.DataFrame:
    """
    Impute missing alloy composition using Alloy Family average.
    """
    logger.info("Imputing composition...")
    df_imp = df.copy()
    # Logic depends on how composition is stored (string vs dict vs array)
    # Assuming 'alloy_composition' is a string or object that can be averaged if numeric
    # For this implementation, we assume a helper exists or we fill with family mean if numeric
    if 'alloy_family' in df_imp.columns and 'alloy_composition' in df_imp.columns:
        # Placeholder for actual imputation logic based on family averages
        pass 
    return df_imp

def impute_grain_size_knn(df: pd.DataFrame, k: int = 5) -> pd.DataFrame:
    """
    KNN grain size imputation using imputed composition and strain_rate as predictors.
    """
    logger.info(f"Imputing grain size using KNN (k={k})...")
    df_imp = df.copy()
    # Logic would use sklearn.neighbors.KNeighborsRegressor
    # Predictors: composition (encoded), strain_rate
    # Target: grain_size
    return df_imp

def encode_elemental_fractions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Encode alloy composition into high-dimensional elemental fraction vector.
    """
    logger.info("Encoding elemental fractions...")
    # Logic to parse composition string into 10-dim vector
    return df

def perform_stratified_split(
    df: pd.DataFrame, 
    stratum_col: str = 'alloy_family',
    test_size: float = TEST_SIZE,
    random_state: int = STRATIFIED_SPLIT_SEED,
    min_stratum_size: int = MIN_STRATUM_SIZE
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Perform stratified split by Alloy Family.
    Ensures N >= min_stratum_size per stratum in the original data (or raises warning/filters).
    
    Args:
        df: Input DataFrame (expected to be 'data/processed/encoded_features.csv' or similar)
        stratum_col: Column name for stratification (default: 'alloy_family')
        test_size: Proportion of data to include in test set
        random_state: Random seed for reproducibility
        min_stratum_size: Minimum records required per stratum to be included in split
    
    Returns:
        Tuple of (train_df, test_df)
    """
    logger.info(f"Performing stratified split on column '{stratum_col}'...")
    
    if stratum_col not in df.columns:
        raise ValueError(f"Stratification column '{stratum_col}' not found in DataFrame.")
    
    # Filter out strata with fewer than min_stratum_size records
    stratum_counts = df[stratum_col].value_counts()
    valid_strata = stratum_counts[stratum_counts >= min_stratum_size].index
    df_filtered = df[df[stratum_col].isin(valid_strata)]
    
    dropped_strata = set(stratum_counts.index) - set(valid_strata)
    if dropped_strata:
        logger.warning(f"Excluded strata with N < {min_stratum_size}: {list(dropped_strata)}")
    
    if len(df_filtered) < 2:
        raise ValueError("Not enough data remaining after filtering strata to perform split.")
    
    # Perform split
    from sklearn.model_selection import train_test_split
    
    train_df, test_df = train_test_split(
        df_filtered,
        test_size=test_size,
        random_state=random_state,
        stratify=df_filtered[stratum_col]
    )
    
    logger.info(f"Train set size: {len(train_df)}, Test set size: {len(test_df)}")
    logger.info(f"Train set stratum distribution:\n{train_df[stratum_col].value_counts()}")
    logger.info(f"Test set stratum distribution:\n{test_df[stratum_col].value_counts()}")
    
    return train_df, test_df

def main():
    """
    Main entry point to execute the stratified split (T017).
    Assumes previous steps have generated 'data/processed/encoded_features.csv'.
    Outputs: 'data/processed/train.csv', 'data/processed/test.csv'
    """
    logger.info("Starting T017: Stratified Split")
    
    input_file = DATA_PROCESSED_DIR / "encoded_features.csv"
    train_output = DATA_PROCESSED_DIR / "train.csv"
    test_output = DATA_PROCESSED_DIR / "test.csv"
    
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        logger.error("Please ensure T016 (encode_elemental_fractions) has completed successfully.")
        sys.exit(1)
    
    logger.info(f"Loading data from {input_file}")
    df = pd.read_csv(input_file)
    
    # Execute split
    train_df, test_df = perform_stratified_split(df)
    
    # Save outputs
    logger.info(f"Saving train set to {train_output}")
    train_df.to_csv(train_output, index=False)
    
    logger.info(f"Saving test set to {test_output}")
    test_df.to_csv(test_output, index=False)
    
    logger.info("T017 completed successfully.")
    return train_df, test_df

if __name__ == "__main__":
    main()