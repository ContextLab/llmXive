import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

import pandas as pd

from utils.logger import get_logger
from data.config import get_config

# Configure logger for this module
logger = get_logger(__name__)

def validate_imputed_data(input_path: str, output_path: str) -> Dict[str, Any]:
    """
    Verify that the imputed data file exists, is non-empty, and contains valid data.
    
    Args:
        input_path: Path to the imputed data CSV file.
        output_path: Path where the validation result JSON will be written.
        
    Returns:
        A dictionary containing the validation status and metadata.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the file is empty or contains no valid rows.
    """
    logger.info(f"Validating imputed data at: {input_path}")
    
    input_file = Path(input_path)
    
    # Check if file exists
    if not input_file.exists():
        raise FileNotFoundError(f"Imputed data file not found: {input_path}")
    
    # Load data
    try:
        df = pd.read_csv(input_file)
    except Exception as e:
        raise ValueError(f"Failed to read CSV file: {e}")
    
    # Check if file is empty
    if df.empty:
        raise ValueError("Imputed data file is empty (0 rows).")
    
    # Validate required columns (based on dataset.schema.yaml)
    required_columns = [
        'participant_id', 
        'pre_self_esteem', 
        'post_self_esteem', 
        'comparison_tendency', 
        'avatar_condition'
    ]
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        logger.warning(f"Missing required columns: {missing_columns}")
        # We proceed but note the missing columns in the status
        status = "pass_with_warnings"
    else:
        status = "pass"
    
    # Check for NaN values in key columns (should be none after imputation)
    key_numeric_cols = ['pre_self_esteem', 'post_self_esteem', 'comparison_tendency']
    nan_counts = df[key_numeric_cols].isna().sum()
    total_nans = nan_counts.sum()
    
    if total_nans > 0:
        logger.warning(f"Found {total_nans} NaN values in key columns after imputation.")
        status = "pass_with_warnings"
    else:
        logger.info("No NaN values found in key columns.")
    
    # Prepare validation result
    validation_result = {
        "status": status,
        "imputation_success": True,
        "row_count": len(df),
        "column_count": len(df.columns),
        "missing_columns": missing_columns,
        "nan_counts_in_key_cols": nan_counts.to_dict(),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Write result to JSON
    with open(output_file, 'w') as f:
        json.dump(validation_result, f, indent=2)
    
    logger.info(f"Validation result written to: {output_path}")
    logger.info(f"Status: {status}, Rows: {len(df)}")
    
    return validation_result

def save_validation_result(result: Dict[str, Any], output_path: str) -> None:
    """
    Save the validation result dictionary to a JSON file.
    
    Args:
        result: The validation result dictionary.
        output_path: Path where the JSON file will be saved.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Validation result saved to: {output_path}")

def run_validation() -> Dict[str, Any]:
    """
    Main entry point for the validation script.
    Reads configuration, validates the imputed data, and writes the result.
    
    Returns:
        The validation result dictionary.
    """
    config = get_config()
    
    input_path = config.get('paths', {}).get('imputed_data', 'data/processed/imputed_data.csv')
    output_path = config.get('paths', {}).get('post_imputation_validation', 'data/processed/post_imputation_validation.json')
    
    try:
        result = validate_imputed_data(input_path, output_path)
        return result
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        # Create a failure result
        failure_result = {
            "status": "fail",
            "imputation_success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        save_validation_result(failure_result, output_path)
        return failure_result
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        # Create a failure result
        failure_result = {
            "status": "fail",
            "imputation_success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        save_validation_result(failure_result, output_path)
        return failure_result

def main():
    """
    Command-line entry point.
    """
    logging.basicConfig(level=logging.INFO)
    result = run_validation()
    if result['status'] == 'fail':
        logger.error("Validation failed.")
        sys.exit(1)
    else:
        logger.info("Validation completed successfully.")
        sys.exit(0)

if __name__ == "__main__":
    import sys
    main()