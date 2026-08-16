"""
Validation utilities for the cognitive flexibility prediction pipeline.

This module provides functions to validate the integrity and structure of
processed data artifacts, ensuring data quality before analysis.
"""
import os
import logging
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any

from code.data.paths import get_processed_path, ensure_dir
from code.utils.logging import log_error, log_warning, init_logging

logger = logging.getLogger(__name__)

def validate_final_results_schema(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate that the DataFrame has the required columns and types for final_results.csv.
    
    Args:
        df: DataFrame to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    required_columns = [
        'Subject_ID', 'Variability_Metric', 'Flexibility_Score', 
        'Covariates', 'Predicted_Score', 'Residual', 
        'Beta_Variability', 'SE_Variability', 'P_Value'
    ]
    
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")
    
    # Check for null values in critical columns
    critical_cols = ['Subject_ID', 'Variability_Metric', 'Flexibility_Score']
    for col in critical_cols:
        if col in df.columns and df[col].isnull().any():
            errors.append(f"Column '{col}' contains null values")
    
    # Check data types
    if 'Subject_ID' in df.columns and not df['Subject_ID'].dtype == 'object':
        errors.append(f"Column 'Subject_ID' should be string type, got {df['Subject_ID'].dtype}")
        
    if 'Variability_Metric' in df.columns and not pd.api.types.is_numeric_dtype(df['Variability_Metric']):
        errors.append(f"Column 'Variability_Metric' should be numeric, got {df['Variability_Metric'].dtype}")
        
    if 'Flexibility_Score' in df.columns and not pd.api.types.is_numeric_dtype(df['Flexibility_Score']):
        errors.append(f"Column 'Flexibility_Score' should be numeric, got {df['Flexibility_Score'].dtype}")
    
    return len(errors) == 0, errors

def validate_unique_subjects(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate that each subject appears exactly once in the DataFrame.
    
    Args:
        df: DataFrame to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    if 'Subject_ID' not in df.columns:
        errors.append("Column 'Subject_ID' not found in DataFrame")
        return False, errors
    
    subject_counts = df['Subject_ID'].value_counts()
    duplicates = subject_counts[subject_counts > 1]
    
    if len(duplicates) > 0:
        duplicate_subjects = duplicates.index.tolist()
        errors.append(f"Found duplicate Subject_IDs: {duplicate_subjects}")
        errors.append(f"Total duplicate entries: {len(duplicates)}")
    
    return len(errors) == 0, errors

def validate_final_results_file(filepath: Optional[str] = None) -> Tuple[bool, List[str], int]:
    """
    Validate the final_results.csv file for schema correctness and unique subjects.
    
    Args:
        filepath: Optional path to the file. If None, uses default path from config.
        
    Returns:
        Tuple of (is_valid, list_of_errors, row_count)
    """
    if filepath is None:
        processed_path = get_processed_path()
        filepath = os.path.join(processed_path, 'final_results.csv')
    
    if not os.path.exists(filepath):
        return False, [f"File not found: {filepath}"], 0
    
    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        return False, [f"Failed to read CSV: {str(e)}"], 0
    
    if df.empty:
        return False, ["DataFrame is empty"], 0
    
    row_count = len(df)
    errors = []
    
    # Validate schema
    schema_valid, schema_errors = validate_final_results_schema(df)
    errors.extend(schema_errors)
    
    # Validate unique subjects
    unique_valid, unique_errors = validate_unique_subjects(df)
    errors.extend(unique_errors)
    
    is_valid = schema_valid and unique_valid
    
    if not is_valid:
        log_error(f"Validation failed for {filepath}: {errors}")
    else:
        logger.info(f"Validation passed for {filepath}: {row_count} unique subjects")
    
    return is_valid, errors, row_count

def run_validation_pipeline(filepath: Optional[str] = None) -> Dict[str, Any]:
    """
    Run the complete validation pipeline for final_results.csv.
    
    Args:
        filepath: Optional path to the file. If None, uses default path.
        
    Returns:
        Dictionary with validation results:
        - valid: bool
        - errors: list of error messages
        - row_count: number of rows
        - unique_subjects: number of unique subjects
    """
    is_valid, errors, row_count = validate_final_results_file(filepath)
    
    processed_path = get_processed_path()
    default_filepath = os.path.join(processed_path, 'final_results.csv')
    actual_filepath = filepath if filepath else default_filepath
    
    if not is_valid:
        log_error(f"Validation failed for {actual_filepath}")
        for err in errors:
            log_error(f"  - {err}")
    else:
        logger.info(f"Validation successful for {actual_filepath}")
        logger.info(f"  - Total rows: {row_count}")
        if 'Subject_ID' in pd.read_csv(actual_filepath).columns:
            df = pd.read_csv(actual_filepath)
            unique_count = df['Subject_ID'].nunique()
            logger.info(f"  - Unique subjects: {unique_count}")
    
    return {
        'valid': is_valid,
        'errors': errors,
        'row_count': row_count,
        'unique_subjects': row_count if is_valid else 0,
        'filepath': actual_filepath
    }
