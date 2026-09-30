"""
Feature Engineering Module (T017)

Merges traditional molecular descriptors with TDA features to create a combined
feature matrix for downstream modeling.

Inputs:
    data/processed/traditional_descriptors.csv
    data/processed/tda_features.csv
Output:
    data/processed/combined_features.csv
"""
import os
import sys
import logging
from pathlib import Path
from typing import Tuple, Optional

import pandas as pd

# Configure project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
INPUT_TRADITIONAL = DATA_PROCESSED_DIR / "traditional_descriptors.csv"
INPUT_TDA = DATA_PROCESSED_DIR / "tda_features.csv"
OUTPUT_COMBINED = DATA_PROCESSED_DIR / "combined_features.csv"
LOGS_DIR = PROJECT_ROOT / "data" / "logs"

def setup_logging() -> logging.Logger:
    """Setup logging configuration for the feature engineering module."""
    os.makedirs(LOGS_DIR, exist_ok=True)
    log_file = LOGS_DIR / "feature_engineering.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def load_traditional_descriptors(logger: logging.Logger) -> pd.DataFrame:
    """
    Load the traditional molecular descriptors from CSV.
    
    Args:
        logger: Logger instance for recording progress/errors.
        
    Returns:
        DataFrame containing molecular descriptors.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If required columns are missing.
    """
    logger.info(f"Loading traditional descriptors from: {INPUT_TRADITIONAL}")
    
    if not INPUT_TRADITIONAL.exists():
        logger.error(f"Input file not found: {INPUT_TRADITIONAL}")
        raise FileNotFoundError(f"Input file not found: {INPUT_TRADITIONAL}")
    
    df = pd.read_csv(INPUT_TRADITIONAL)
    
    required_cols = {"molecule_id", "MW", "logP"}
    missing_cols = required_cols - set(df.columns)
    
    if missing_cols:
        logger.error(f"Missing required columns in traditional descriptors: {missing_cols}")
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    logger.info(f"Loaded {len(df)} rows from traditional descriptors.")
    return df

def load_tda_features(logger: logging.Logger) -> pd.DataFrame:
    """
    Load the TDA features (persistence images) from CSV.
    
    Args:
        logger: Logger instance for recording progress/errors.
        
    Returns:
        DataFrame containing TDA features.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If required columns are missing.
    """
    logger.info(f"Loading TDA features from: {INPUT_TDA}")
    
    if not INPUT_TDA.exists():
        logger.error(f"Input file not found: {INPUT_TDA}")
        raise FileNotFoundError(f"Input file not found: {INPUT_TDA}")
    
    df = pd.read_csv(INPUT_TDA)
    
    # Verify at least molecule_id exists; TDA columns are dynamic (p_img_0...p_img_99)
    if "molecule_id" not in df.columns:
        logger.error("Missing required column 'molecule_id' in TDA features.")
        raise ValueError("Missing required column 'molecule_id' in TDA features.")
    
    logger.info(f"Loaded {len(df)} rows from TDA features.")
    return df

def merge_features(
    traditional_df: pd.DataFrame, 
    tda_df: pd.DataFrame, 
    logger: logging.Logger
) -> pd.DataFrame:
    """
    Merge traditional and TDA feature DataFrames on 'molecule_id'.
    
    Args:
        traditional_df: DataFrame of traditional descriptors.
        tda_df: DataFrame of TDA features.
        logger: Logger instance.
        
    Returns:
        Merged DataFrame.
        
    Raises:
        ValueError: If merge results in unexpected row count.
    """
    logger.info("Merging feature sets on 'molecule_id'...")
    
    # Perform inner join to ensure we only keep molecules present in both sets
    merged_df = pd.merge(
        traditional_df, 
        tda_df, 
        on="molecule_id", 
        how="inner"
    )
    
    expected_rows = min(len(traditional_df), len(tda_df))
    actual_rows = len(merged_df)
    
    if actual_rows == 0:
        logger.error("Merge resulted in zero rows. Check for mismatched molecule IDs.")
        raise ValueError("Merge resulted in zero rows.")
    
    logger.info(f"Merged successfully. Rows: {actual_rows} (Traditional: {len(traditional_df)}, TDA: {len(tda_df)})")
    return merged_df

def prepare_combined_feature_matrix(df: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    """
    Finalize the combined feature matrix (ensure correct dtypes, no nulls in key cols).
    
    Args:
        df: Merged DataFrame.
        logger: Logger instance.
        
    Returns:
        Cleaned DataFrame ready for modeling.
    """
    logger.info("Validating and preparing combined feature matrix...")
    
    # Ensure molecule_id is string
    df["molecule_id"] = df["molecule_id"].astype(str)
    
    # Check for nulls in critical columns (MW, logP, and all TDA columns)
    tda_cols = [col for col in df.columns if col.startswith("p_img_")]
    numeric_cols = ["MW", "logP"] + tda_cols
    
    null_counts = df[numeric_cols].isnull().sum()
    if null_counts.any():
        logger.warning(f"Found null values in numeric columns:\n{null_counts[null_counts > 0]}")
        # Drop rows with any nulls in numeric features to ensure model compatibility
        drop_indices = df[df[numeric_cols].isnull().any(axis=1)].index
        if len(drop_indices) > 0:
            logger.info(f"Dropping {len(drop_indices)} rows with null values.")
            df = df.drop(index=drop_indices)
    
    logger.info(f"Final combined matrix shape: {df.shape}")
    return df

def save_combined_features(df: pd.DataFrame, logger: logging.Logger) -> None:
    """
    Save the combined feature matrix to CSV.
    
    Args:
        df: Final combined DataFrame.
        logger: Logger instance.
    """
    logger.info(f"Saving combined features to: {OUTPUT_COMBINED}")
    
    os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)
    df.to_csv(OUTPUT_COMBINED, index=False)
    
    if OUTPUT_COMBINED.exists():
        logger.info("Successfully saved combined features.")
    else:
        logger.error("Failed to save combined features.")
        raise IOError("Failed to write output file.")

def run_feature_engineering() -> None:
    """
    Main orchestration function for feature engineering.
    """
    logger = setup_logging()
    logger.info("Starting Feature Engineering (T017)...")
    
    try:
        # Load inputs
        traditional_df = load_traditional_descriptors(logger)
        tda_df = load_tda_features(logger)
        
        # Merge
        merged_df = merge_features(traditional_df, tda_df, logger)
        
        # Prepare
        final_df = prepare_combined_feature_matrix(merged_df, logger)
        
        # Save
        save_combined_features(final_df, logger)
        
        logger.info("Feature Engineering completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data file error: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during feature engineering: {e}")
        sys.exit(1)

def main() -> None:
    """Entry point."""
    run_feature_engineering()

if __name__ == "__main__":
    main()
