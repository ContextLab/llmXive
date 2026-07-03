"""
Data validation module for eye-tracking datasets.
Validates presence of critical variables, checks data content,
applies ROI fallbacks, and generates validation reports.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd

from config import get_config
from utils.logging import get_logger

# Define critical variables required for analysis
CRITICAL_VARS = [
    'gaze_coordinates',
    'response_times',
    'emotion_labels',
    'roi_annotations'
]

def get_logger_wrapper():
    """Get a logger instance for this module."""
    return get_logger(__name__)

def check_variable_presence(df: pd.DataFrame, variables: List[str]) -> Dict[str, bool]:
    """
    Check if specified variables are present in the DataFrame.
    
    Args:
        df: Input DataFrame
        variables: List of variable names to check
        
    Returns:
        Dictionary mapping variable names to presence status
    """
    logger = get_logger_wrapper()
    result = {}
    
    for var in variables:
        is_present = var in df.columns
        result[var] = is_present
        if not is_present:
            logger.warning(f"Critical variable '{var}' is missing from dataset")
        
    return result

def validate_data_content(df: pd.DataFrame, variable: str) -> bool:
    """
    Validate that a variable contains non-empty, non-null data.
    
    Args:
        df: Input DataFrame
        variable: Variable name to validate
        
    Returns:
        True if variable has valid content, False otherwise
    """
    logger = get_logger_wrapper()
    
    if variable not in df.columns:
        logger.debug(f"Variable '{variable}' does not exist in DataFrame")
        return False
    
    # Check for empty or all-None values
    col_data = df[variable]
    
    if col_data.empty:
        logger.debug(f"Variable '{variable}' is empty")
        return False
    
    # Check if all values are None or NaN
    if col_data.isna().all():
        logger.debug(f"Variable '{variable}' contains only null values")
        return False
    
    # For list-like columns, check if any entries are None
    if col_data.apply(lambda x: isinstance(x, (list, dict))).any():
        non_null_count = col_data.apply(lambda x: x is not None and len(x) > 0 if isinstance(x, (list, dict)) else True).sum()
        if non_null_count == 0:
            logger.debug(f"Variable '{variable}' contains only empty list/dict values")
            return False
    
    return True

def apply_roi_fallback(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply generic ROI fallback (3x3 grid) if roi_annotations are missing.
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with roi_annotations column added if missing
    """
    logger = get_logger_wrapper()
    
    if 'roi_annotations' not in df.columns:
        logger.info("Applying generic ROI fallback (3x3 grid) for missing roi_annotations")
        
        # Create a default 3x3 grid annotation for each row
        # Format: list of 9 regions with coordinates
        default_roi = [
            {'x': 0, 'y': 0, 'w': 33, 'h': 33},
            {'x': 33, 'y': 0, 'w': 34, 'h': 33},
            {'x': 67, 'y': 0, 'w': 33, 'h': 33},
            {'x': 0, 'y': 33, 'w': 33, 'h': 34},
            {'x': 33, 'y': 33, 'w': 34, 'h': 34},
            {'x': 67, 'y': 33, 'w': 33, 'h': 34},
            {'x': 0, 'y': 67, 'w': 33, 'h': 33},
            {'x': 33, 'y': 67, 'w': 34, 'h': 33},
            {'x': 67, 'y': 67, 'w': 33, 'h': 33}
        ]
        
        df = df.copy()
        df['roi_annotations'] = [default_roi] * len(df)
        logger.info(f"Applied ROI fallback to {len(df)} records")
    
    return df

def write_validation_report(report: Dict[str, Any], output_path: Path) -> None:
    """
    Write validation report to JSON file.
    
    Args:
        report: Validation report dictionary
        output_path: Path to output file
    """
    logger = get_logger_wrapper()
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Validation report written to {output_path}")

def validate_dataset(dataset_path: Path, output_path: Path) -> Dict[str, Any]:
    """
    Perform full validation on a dataset.
    
    Args:
        dataset_path: Path to input dataset
        output_path: Path to write validation report
        
    Returns:
        Validation report dictionary
        
    Raises:
        SystemExit: If critical variables are missing
    """
    logger = get_logger_wrapper()
    logger.info(f"Starting validation for dataset: {dataset_path}")
    
    # Load dataset
    try:
        df = pd.read_csv(dataset_path)
        logger.info(f"Loaded dataset with {len(df)} records")
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise
    
    # Check variable presence
    presence_result = check_variable_presence(df, CRITICAL_VARS)
    missing_vars = [var for var, present in presence_result.items() if not present]
    
    # Validate data content for present variables
    content_valid = {}
    for var in CRITICAL_VARS:
        if presence_result[var]:
            content_valid[var] = validate_data_content(df, var)
        else:
            content_valid[var] = False
    
    # Check for critical variables missing
    critical_missing = [var for var in missing_vars if var in CRITICAL_VARS]
    
    # Apply ROI fallback if roi_annotations is missing but others are present
    if 'roi_annotations' in critical_missing and len(critical_missing) == 1:
        logger.info("Applying ROI fallback as only roi_annotations is missing")
        df = apply_roi_fallback(df)
        critical_missing.remove('roi_annotations')
        content_valid['roi_annotations'] = True
    
    # Determine overall status
    if len(critical_missing) > 0:
        status = 'FAIL'
        logger.error(f"Validation failed. Missing critical variables: {critical_missing}")
    else:
        # Check if all present variables have valid content
        if all(content_valid.values()):
            status = 'PASS'
            logger.info("Validation passed. All critical variables present and valid.")
        else:
            status = 'FAIL'
            invalid_vars = [var for var, valid in content_valid.items() if not valid]
            logger.error(f"Validation failed. Invalid content in variables: {invalid_vars}")
    
    # Build report
    report = {
        'status': status,
        'dataset_path': str(dataset_path),
        'record_count': len(df),
        'variable_presence': presence_result,
        'content_validation': content_valid,
        'missing_critical_vars': critical_missing,
        'roi_fallback_applied': 'roi_annotations' not in missing_vars and 'roi_annotations' in df.columns
    }
    
    # Write report
    write_validation_report(report, output_path)
    
    # Exit with error if critical variables missing
    if status == 'FAIL':
        logger.error("Halting due to missing critical variables.")
        sys.exit(1)
    
    return report

def main():
    """Main entry point for validation script."""
    logger = get_logger_wrapper()
    config = get_config()
    
    # Default paths
    dataset_path = config.data_dir / "raw" / "dataset.csv"
    output_path = config.data_dir / "processed" / "validation_report.json"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Run validation
    validate_dataset(dataset_path, output_path)
    
    logger.info("Validation complete.")

if __name__ == "__main__":
    main()