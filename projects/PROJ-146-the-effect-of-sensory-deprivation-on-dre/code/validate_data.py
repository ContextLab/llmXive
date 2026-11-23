import os
import sys
import logging
import pandas as pd
import numpy as np
from logging_config import setup_logging

logger = logging.getLogger(__name__)

def validate_recall_binary(df: pd.DataFrame) -> tuple[bool, list[str]]:
    """
    Validates that the 'recall' column contains only binary values (0 or 1).
    
    Args:
        df: The dataframe to validate.
        
    Returns:
        A tuple of (is_valid, list_of_errors).
    """
    errors = []
    if 'recall' not in df.columns:
        errors.append("Column 'recall' is missing from the dataframe.")
        return False, errors
    
    recall_series = df['recall']
    
    # Check for non-numeric types
    if not pd.api.types.is_numeric_dtype(recall_series):
        errors.append(f"Column 'recall' is not numeric. Dtype: {recall_series.dtype}")
        return False, errors
    
    # Check for nulls
    if recall_series.isna().any():
        null_count = recall_series.isna().sum()
        errors.append(f"Column 'recall' contains {null_count} null values.")
    
    # Check for values outside {0, 1}
    unique_values = set(recall_series.dropna().unique())
    allowed_values = {0, 1, 0.0, 1.0} # Handle potential float vs int representation
    
    invalid_values = unique_values - allowed_values
    if invalid_values:
        errors.append(f"Column 'recall' contains invalid values: {invalid_values}. Expected only 0 or 1.")
        return False, errors
    
    # Ensure strictly 0 or 1 (cast to int for final check if needed, but set comparison above covers logic)
    # If the column is float64 with 0.0 and 1.0, it's logically binary.
    # We accept 0, 1, 0.0, 1.0.
    
    return True, errors

def validate_bizarreness_range(df: pd.DataFrame) -> tuple[bool, list[str]]:
    """
    Validates that the 'bizarreness' column contains integers between 1 and 7 inclusive.
    
    Args:
        df: The dataframe to validate.
        
    Returns:
        A tuple of (is_valid, list_of_errors).
    """
    errors = []
    if 'bizarreness' not in df.columns:
        errors.append("Column 'bizarreness' is missing from the dataframe.")
        return False, errors
    
    bizarreness_series = df['bizarreness']
    
    # Check for nulls
    if bizarreness_series.isna().any():
        null_count = bizarreness_series.isna().sum()
        errors.append(f"Column 'bizarreness' contains {null_count} null values.")
    
    # Check for non-integer types (or floats that are effectively integers)
    # We allow int64, int32, float64 (if values are whole numbers)
    if not pd.api.types.is_numeric_dtype(bizarreness_series):
        errors.append(f"Column 'bizarreness' is not numeric. Dtype: {bizarreness_series.dtype}")
        return False, errors
    
    # Check for non-integer values if dtype is float
    if pd.api.types.is_float_dtype(bizarreness_series):
        non_integer_mask = ~bizarreness_series.is_integer()
        if non_integer_mask.any():
            errors.append(f"Column 'bizarreness' contains non-integer values.")
            return False, errors
    
    # Check range [1, 7]
    valid_mask = (bizarreness_series >= 1) & (bizarreness_series <= 7)
    invalid_count = (~valid_mask).sum()
    
    if invalid_count > 0:
        invalid_values = bizarreness_series[~valid_mask].unique()
        errors.append(f"Column 'bizarreness' contains {invalid_count} values outside range [1, 7]. Found: {invalid_values}")
        return False, errors
        
    return True, errors

def run_validation(df: pd.DataFrame, source_name: str = "unknown") -> bool:
    """
    Runs all validations on the dataframe. Logs results and returns overall success status.
    
    Args:
        df: The dataframe to validate.
        source_name: Identifier for the source of the data (for logging).
        
    Returns:
        True if all validations pass, False otherwise.
    """
    logger.info(f"Running validation on data from source: {source_name}")
    all_valid = True
    
    # Validate Recall
    recall_valid, recall_errors = validate_recall_binary(df)
    if not recall_valid:
        all_valid = False
        for err in recall_errors:
            logger.error(f"[Recall Validation] {err}")
    else:
        logger.info("[Recall Validation] Passed: Values are binary (0/1).")
        
    # Validate Bizarreness
    bizarreness_valid, bizarreness_errors = validate_bizarreness_range(df)
    if not bizarreness_valid:
        all_valid = False
        for err in bizarreness_errors:
            logger.error(f"[Bizarreness Validation] {err}")
    else:
        logger.info("[Bizarreness Validation] Passed: Values are integers 1-7.")
        
    if all_valid:
        logger.info(f"Validation SUCCESS for {source_name}.")
    else:
        logger.error(f"Validation FAILED for {source_name}. See errors above.")
        
    return all_valid

def main():
    """
    Entry point for standalone execution.
    Expects a CSV file path as the first argument.
    """
    setup_logging()
    
    if len(sys.argv) < 2:
        logger.error("Usage: python validate_data.py <path_to_csv>")
        sys.exit(1)
        
    csv_path = sys.argv[1]
    
    if not os.path.exists(csv_path):
        logger.error(f"File not found: {csv_path}")
        sys.exit(1)
        
    try:
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(df)} rows from {csv_path}")
        
        success = run_validation(df, source_name=os.path.basename(csv_path))
        
        if not success:
            sys.exit(1)
            
    except Exception as e:
        logger.exception(f"Error processing file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
