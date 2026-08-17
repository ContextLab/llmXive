import os
import sys
import logging
from pathlib import Path
from typing import List, Tuple, Optional
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Expected columns for the features dataset
METRIC_COLUMNS = ['cc', 'halstead', 'loc']
TARGET_COLUMN = 'is_buggy'
REQUIRED_COLUMNS = ['file_path'] + METRIC_COLUMNS + [TARGET_COLUMN]

def validate_no_nan_in_metrics(df: pd.DataFrame, metric_columns: Optional[List[str]] = None) -> Tuple[bool, List[str]]:
    """
    Validates that there are no NaN values in the specified metric columns.
    
    Args:
        df: The DataFrame containing the metrics.
        metric_columns: List of column names to check. Defaults to METRIC_COLUMNS.
        
    Returns:
        Tuple of (is_valid, list_of_invalid_columns).
        is_valid is True if no NaNs are found in the specified columns.
    """
    if metric_columns is None:
        metric_columns = METRIC_COLUMNS
    
    invalid_columns = []
    for col in metric_columns:
        if col not in df.columns:
            logger.error(f"Required column '{col}' is missing from DataFrame.")
            invalid_columns.append(col)
            continue
        
        if df[col].isna().any():
            nan_count = df[col].isna().sum()
            logger.error(f"Column '{col}' contains {nan_count} NaN values.")
            invalid_columns.append(col)
        else:
            logger.info(f"Column '{col}' validation passed: No NaN values found.")
    
    return len(invalid_columns) == 0, invalid_columns

def validate_schema_and_metrics(df: pd.DataFrame) -> bool:
    """
    Validates the DataFrame schema (required columns) and checks for NaNs in metrics.
    
    Args:
        df: The DataFrame to validate.
        
    Returns:
        True if validation passes, False otherwise.
    """
    # Check schema
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        logger.error(f"Schema validation failed. Missing columns: {missing_cols}")
        return False
    
    logger.info("Schema validation passed.")
    
    # Check for NaNs in metrics
    is_valid, invalid_cols = validate_no_nan_in_metrics(df)
    if not is_valid:
        logger.error(f"Metric validation failed. Columns with NaN: {invalid_cols}")
        return False
    
    return True

def main():
    """
    Main entry point for standalone execution.
    Expects the path to the features CSV as the first argument.
    """
    if len(sys.argv) < 2:
        print("Usage: python -m src.validate_metrics <path_to_features.csv>")
        sys.exit(1)
    
    csv_path = Path(sys.argv[1])
    if not csv_path.exists():
        logger.error(f"File not found: {csv_path}")
        sys.exit(1)
    
    logger.info(f"Loading data from {csv_path}...")
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        logger.error(f"Failed to load CSV: {e}")
        sys.exit(1)
    
    logger.info(f"Loaded {len(df)} rows.")
    
    if validate_schema_and_metrics(df):
        logger.info("Validation successful: No NaN values in metric columns.")
        sys.exit(0)
    else:
        logger.error("Validation failed: NaN values detected or schema mismatch.")
        sys.exit(1)

if __name__ == '__main__':
    main()