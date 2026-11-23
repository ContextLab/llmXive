"""
Validation utilities for data schemas and merged cohorts.
"""
import pandas as pd
from typing import List, Dict, Any, Optional
from .logging_utils import get_logger

logger = get_logger(__name__)

def validate_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> bool:
    """Validate DataFrame against a schema definition."""
    logger.info("Validating schema...")
    
    for col, dtype in schema.items():
        if col not in df.columns:
            logger.error(f"Missing column in schema validation: {col}")
            return False
        
        # Check dtype compatibility (simplified)
        if dtype == 'str' and not pd.api.types.is_object_dtype(df[col]):
            logger.warning(f"Column {col} expected str but got {df[col].dtype}")
        elif dtype == 'float' and not pd.api.types.is_float_dtype(df[col]):
            logger.warning(f"Column {col} expected float but got {df[col].dtype}")
        elif dtype == 'int' and not pd.api.types.is_integer_dtype(df[col]):
            logger.warning(f"Column {col} expected int but got {df[col].dtype}")
    
    logger.info("Schema validation passed")
    return True

def validate_non_null(df: pd.DataFrame, columns: List[str]) -> bool:
    """Validate that specified columns have no null values."""
    logger.info("Validating non-null constraints...")
    
    for col in columns:
        if col not in df.columns:
            logger.error(f"Column {col} not found for non-null validation")
            return False
        
        null_count = df[col].isnull().sum()
        if null_count > 0:
            logger.error(f"Column {col} has {null_count} null values")
            return False
    
    logger.info("Non-null validation passed")
    return True

def validate_merged_cohort(df: pd.DataFrame) -> bool:
    """Validate the merged cohort dataset."""
    logger.info("Validating merged cohort...")
    
    required_columns = [
        'Participant ID', 'Shannon Diversity', 'Sleep Duration', 
        'Sleep Quality', 'Chronotype', 'Age', 'BMI', 
        'Antibiotic History', 'Diet Type'
    ]
    
    # Check required columns
    if not validate_non_null(df, required_columns):
        logger.error("Merged cohort validation failed: missing required columns or null values")
        return False
    
    # Check sample size
    if len(df) == 0:
        logger.warning("Merged cohort is empty")
        return False
    
    logger.info(f"Merged cohort validation passed: {len(df)} participants")
    return True
