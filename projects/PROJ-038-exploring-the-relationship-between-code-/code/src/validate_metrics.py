"""
Validation module for ensuring metric data quality.

This module provides functions to validate the integrity of the features.csv dataset,
specifically checking for missing values (NaN) in numeric metric columns.
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Tuple, Optional

import pandas as pd

# Add parent directory to path for imports if running as script
if str(Path(__file__).parent.parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config import get_memory_limit_bytes

logger = logging.getLogger(__name__)

# Expected numeric metric columns based on T017 specification
NUMERIC_METRIC_COLUMNS = ['cc', 'halstead', 'loc']
TARGET_COLUMN = 'is_buggy'
FILE_PATH_COLUMN = 'file_path'

def validate_no_nan_in_metrics(df: pd.DataFrame, columns: Optional[List[str]] = None) -> Tuple[bool, int, List[str]]:
    """
    Validates that there are no NaN values in the specified metric columns.
    
    Args:
        df: The DataFrame to validate.
        columns: List of column names to check. Defaults to NUMERIC_METRIC_COLUMNS.
        
    Returns:
        A tuple containing:
        - is_valid (bool): True if no NaNs found, False otherwise.
        - nan_count (int): Total number of NaN values found in checked columns.
        - invalid_rows (List[str]): List of indices (as strings) where NaNs were found.
    """
    if columns is None:
        columns = NUMERIC_METRIC_COLUMNS
    
    # Filter to only columns that actually exist in the dataframe
    existing_cols = [col for col in columns if col in df.columns]
    missing_cols = [col for col in columns if col not in df.columns]
    
    if missing_cols:
        logger.warning(f"Columns {missing_cols} not found in dataframe. Skipping validation for these.")
    
    if not existing_cols:
        logger.error("No valid metric columns found to validate.")
        return False, 0, []
    
    # Check for NaNs in the specified columns
    nan_mask = df[existing_cols].isna().any(axis=1)
    nan_count = df[existing_cols].isna().sum().sum()
    invalid_rows = df[nan_mask].index.tolist()
    
    is_valid = nan_count == 0
    
    if not is_valid:
        logger.error(f"Validation failed: Found {nan_count} NaN values in columns {existing_cols}.")
        logger.error(f"Affected row indices: {invalid_rows[:10]}{'...' if len(invalid_rows) > 10 else ''}")
    else:
        logger.info(f"Validation passed: No NaN values found in columns {existing_cols}.")
        
    return is_valid, nan_count, [str(i) for i in invalid_rows]

def validate_schema_and_metrics(df: pd.DataFrame) -> bool:
    """
    Performs a comprehensive validation of the features dataframe.
    
    Checks:
    1. Required columns exist.
    2. No NaN values in numeric metric columns.
    3. No NaN values in the target column.
    4. No NaN values in file paths.
    
    Args:
        df: The DataFrame to validate.
        
    Returns:
        True if all validations pass, False otherwise.
    """
    required_cols = NUMERIC_METRIC_COLUMNS + [TARGET_COLUMN, FILE_PATH_COLUMN]
    
    # Check for missing columns
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        return False
    
    # Validate metrics for NaN
    metrics_valid, _, _ = validate_no_nan_in_metrics(df)
    if not metrics_valid:
        return False
    
    # Validate target for NaN
    if df[TARGET_COLUMN].isna().any():
        logger.error(f"NaN values found in target column '{TARGET_COLUMN}'.")
        return False
        
    # Validate file paths for NaN
    if df[FILE_PATH_COLUMN].isna().any():
        logger.error(f"NaN values found in file path column '{FILE_PATH_COLUMN}'.")
        return False
        
    logger.info("Schema and metric validation passed.")
    return True

def main():
    """
    Main entry point for running validation on the features.csv file.
    Expects the file at code/data/processed/features.csv relative to project root.
    """
    # Determine project root (assuming script is in code/src/)
    project_root = Path(__file__).parent.parent.parent
    features_path = project_root / "code" / "data" / "processed" / "features.csv"
    
    if not features_path.exists():
        logger.error(f"Features file not found at {features_path}")
        sys.exit(1)
        
    logger.info(f"Loading features from {features_path}...")
    try:
        df = pd.read_csv(features_path)
    except Exception as e:
        logger.error(f"Failed to load features file: {e}")
        sys.exit(1)
        
    logger.info(f"Loaded {len(df)} rows.")
    
    if not validate_schema_and_metrics(df):
        logger.error("Validation FAILED. The dataset contains invalid values.")
        sys.exit(1)
    else:
        logger.info("Validation SUCCESS. The dataset is clean.")
        sys.exit(0)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    main()