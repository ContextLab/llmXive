import os
import sys
import logging
from pathlib import Path
from typing import List, Tuple, Optional
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def validate_no_nan_in_metrics(df: pd.DataFrame, metric_columns: List[str]) -> Tuple[bool, List[str]]:
    """
    Validates that no NaN values exist in the specified metric columns of the DataFrame.
    
    Args:
        df: The pandas DataFrame containing the metrics.
        metric_columns: List of column names to check for NaN values (e.g., 'cc', 'halstead', 'loc').
        
    Returns:
        A tuple (is_valid, missing_columns) where:
            - is_valid: True if no NaN values are found in the specified columns.
            - missing_columns: A list of column names that contained NaN values.
            
    Raises:
        ValueError: If the DataFrame is empty or if metric columns are missing.
    """
    if df.empty:
        raise ValueError("The input DataFrame is empty. Cannot validate NaN values.")
        
    missing_cols = []
    
    for col in metric_columns:
        if col not in df.columns:
            raise ValueError(f"Required metric column '{col}' not found in DataFrame. Available columns: {list(df.columns)}")
        
        nan_count = df[col].isna().sum()
        if nan_count > 0:
            missing_cols.append(col)
            logger.warning(f"Found {nan_count} NaN values in column '{col}'.")
        else:
            logger.info(f"Column '{col}' contains no NaN values.")
    
    is_valid = len(missing_cols) == 0
    return is_valid, missing_cols

def validate_schema_and_metrics(df: pd.DataFrame, output_path: Path) -> bool:
    """
    Performs comprehensive validation on the features DataFrame before saving.
    Checks for:
    1. Required columns existence.
    2. No NaN values in metric columns.
    3. No infinite values.
    4. Positive values for LOC and CC (logical constraints).
    
    Args:
        df: The pandas DataFrame to validate.
        output_path: The intended output path (used for logging context).
        
    Returns:
        True if validation passes, False otherwise.
        
    Raises:
        ValueError: If validation fails.
    """
    required_columns = ['file_path', 'cc', 'halstead', 'loc', 'is_buggy']
    metric_columns = ['cc', 'halstead', 'loc']
    
    # Check required columns
    missing_required = [col for col in required_columns if col not in df.columns]
    if missing_required:
        raise ValueError(f"Missing required columns: {missing_required}")
    
    # Check for NaN in metrics
    is_valid, nan_cols = validate_no_nan_in_metrics(df, metric_columns)
    if not is_valid:
        raise ValueError(f"Validation failed: NaN values found in columns: {nan_cols}. "
                         "The dataset must be cleaned before saving.")
                         
    # Check for infinite values
    for col in metric_columns:
        if df[col].isin([float('inf'), float('-inf')]).any():
            raise ValueError(f"Validation failed: Infinite values found in column '{col}'.")
            
    # Logical constraints (optional but recommended)
    if (df['loc'] < 0).any():
        logger.warning("Found negative LOC values. This may indicate parsing errors.")
    if (df['cc'] < 0).any():
        logger.warning("Found negative Cyclomatic Complexity values. This may indicate parsing errors.")
        
    logger.info(f"Validation passed for {len(df)} rows. Ready to save to {output_path}.")
    return True

def main():
    """
    Entry point for the validation script.
    Expects the path to the features CSV as the first argument.
    If valid, it prints success. If invalid, it exits with code 1.
    """
    if len(sys.argv) < 2:
        print("Usage: python code/src/validate_metrics.py <path_to_features_csv>")
        sys.exit(1)
        
    csv_path = Path(sys.argv[1])
    if not csv_path.exists():
        print(f"Error: File not found: {csv_path}")
        sys.exit(1)
        
    logger.info(f"Loading and validating {csv_path}...")
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        sys.exit(1)
        
    try:
        validate_schema_and_metrics(df, csv_path)
        print("SUCCESS: Validation passed. No NaN values found in metric columns.")
        sys.exit(0)
    except ValueError as e:
        print(f"FAILURE: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
