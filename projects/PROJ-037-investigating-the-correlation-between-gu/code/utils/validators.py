"""
Data validation utilities for the research pipeline.
"""
import pandas as pd
from typing import List, Dict, Any, Optional

from .logging_utils import get_logger

logger = get_logger(__name__)

def validate_schema(df: pd.DataFrame, schema: Dict[str, str]) -> bool:
    """
    Validate that a DataFrame matches a required schema.
    
    Args:
        df: The DataFrame to validate.
        schema: Dict mapping column names to expected dtypes (as strings).
        
    Returns:
        True if valid, False otherwise.
    """
    valid = True
    for col, expected_type in schema.items():
        if col not in df.columns:
            logger.error(f"Missing required column: {col}")
            valid = False
            continue
        
        # Basic type check (string representation)
        actual_type = str(df[col].dtype)
        if expected_type.lower() not in actual_type.lower():
            logger.warning(f"Column {col} has type {actual_type}, expected {expected_type}")
            # We don't fail strictly on type mismatch unless it's critical, 
            # but we log it. For this task, we assume strict validation is needed.
            valid = False
    
    return valid

def validate_non_null(df: pd.DataFrame, columns: Optional[List[str]] = None) -> bool:
    """
    Validate that specified columns (or all columns if None) are non-null.
    
    Args:
        df: The DataFrame to validate.
        columns: List of columns to check. If None, checks all.
        
    Returns:
        True if no nulls found, False otherwise.
    """
    cols_to_check = columns if columns else df.columns
    valid = True
    
    for col in cols_to_check:
        if col not in df.columns:
            logger.error(f"Cannot validate non-null for missing column: {col}")
            valid = False
            continue
        
        null_count = df[col].isnull().sum()
        if null_count > 0:
            logger.warning(f"Column {col} has {null_count} null values.")
            valid = False
    
    return valid

def validate_merged_cohort(df: pd.DataFrame) -> bool:
    """
    Specific validation for the merged cohort dataset.
    
    Checks:
    - participant_id exists and is non-null
    - Required numeric columns are non-null
    - No duplicate participant_ids (if applicable)
    
    Args:
        df: The merged cohort DataFrame.
        
    Returns:
        True if valid, False otherwise.
    """
    logger.info("Validating merged cohort structure...")
    
    # Check schema
    required_schema = {
        "participant_id": "object",
        "shannon": "float64",
        "simpson": "float64",
        "sleep_duration": "float64",
        "sleep_quality": "float64",
        "chronotype": "object"
    }
    
    if not validate_schema(df, required_schema):
        logger.error("Merged cohort failed schema validation.")
        return False
    
    # Check non-null for critical columns
    critical_cols = ["participant_id", "shannon", "sleep_duration"]
    if not validate_non_null(df, critical_cols):
        logger.error("Merged cohort has nulls in critical columns.")
        return False
    
    # Check duplicates
    if df["participant_id"].duplicated().any():
        logger.warning("Merged cohort contains duplicate participant IDs.")
        # Depending on requirements, this might be a hard fail. 
        # For now, we log and return False to be safe.
        return False
        
    logger.info("Merged cohort validation passed.")
    return True