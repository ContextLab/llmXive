import os
import logging
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from code.data.paths import get_processed_path, ensure_dir
from code.utils.logging import log_error, log_warning, init_logging

REQUIRED_COLUMNS = [
    'Subject_ID',
    'Mean_FD',
    'Age',
    'Sex',
    'Flexibility_Score',
    'Variability_Metric',
    'Entropy'
]

def validate_final_results_schema(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validates that the DataFrame contains all required columns.
    
    Args:
        df: DataFrame to validate.
        
    Returns:
        Tuple of (is_valid, list of missing columns).
    """
    if df is None or df.empty:
        return False, ["DataFrame is empty or None"]
    
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        return False, missing_cols
    
    return True, []

def validate_unique_subjects(df: pd.DataFrame) -> Tuple[bool, int]:
    """
    Validates that there is exactly one row per Subject_ID.
    
    Args:
        df: DataFrame to validate.
        
    Returns:
        Tuple of (is_valid, count of duplicate subjects).
    """
    if 'Subject_ID' not in df.columns:
        return False, -1
    
    duplicates = df['Subject_ID'].duplicated().sum()
    if duplicates > 0:
        return False, duplicates
    
    return True, 0

def validate_final_results_file(file_path: str) -> Dict[str, Any]:
    """
    Validates the final_results.csv file for schema and uniqueness.
    
    Args:
        file_path: Path to the CSV file.
        
    Returns:
        Dictionary with validation results.
    """
    result = {
        'valid': False,
        'errors': [],
        'subject_count': 0,
        'row_count': 0
    }
    
    if not os.path.exists(file_path):
        result['errors'].append(f"File not found: {file_path}")
        log_error(f"Validation failed: {result['errors'][0]}")
        return result
    
    try:
        df = pd.read_csv(file_path)
        result['row_count'] = len(df)
        
        # Check schema
        schema_valid, missing_cols = validate_final_results_schema(df)
        if not schema_valid:
            result['errors'].append(f"Missing columns: {missing_cols}")
            log_error(f"Schema validation failed: {missing_cols}")
            return result
        
        # Check uniqueness
        unique_valid, dup_count = validate_unique_subjects(df)
        if not unique_valid:
            result['errors'].append(f"Duplicate subjects found: {dup_count}")
            log_error(f"Uniqueness validation failed: {dup_count} duplicates")
            return result
        
        result['valid'] = True
        result['subject_count'] = len(df['Subject_ID'].unique())
        log_warning(f"Validation successful: {result['subject_count']} unique subjects")
        
    except Exception as e:
        result['errors'].append(f"Error reading file: {str(e)}")
        log_error(f"Validation exception: {str(e)}")
    
    return result

def run_validation_pipeline() -> Dict[str, Any]:
    """
    Main pipeline to validate the final_results.csv file.
    
    Returns:
        Dictionary with validation results.
    """
    init_logging()
    processed_path = get_processed_path()
    ensure_dir(processed_path)
    
    final_results_path = os.path.join(processed_path, 'final_results.csv')
    
    if not os.path.exists(final_results_path):
        log_error(f"Final results file not found at {final_results_path}")
        return {
            'valid': False,
            'errors': [f"File not found: {final_results_path}"],
            'subject_count': 0,
            'row_count': 0
        }
    
    validation_result = validate_final_results_file(final_results_path)
    
    if validation_result['valid']:
        log_warning(f"Validation passed: {validation_result['subject_count']} unique subjects in final_results.csv")
    else:
        log_error(f"Validation failed: {validation_result['errors']}")
    
    return validation_result
