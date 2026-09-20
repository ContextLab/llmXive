import os
import sys
import logging
from pathlib import Path
from typing import List, Set
import pandas as pd
import json
from datetime import datetime

# Import utilities from existing modules
from utils.logger import get_logger
from data.config import get_config

REQUIRED_VARIABLES: Set[str] = {
    'avatar_condition',
    'pre_self_esteem',
    'post_self_esteem',
    'comparison_tendency'
}

def validate_raw_data_variables(df: pd.DataFrame, required_vars: Set[str] = None) -> dict:
    """
    Validates that the DataFrame contains all required variables.

    Args:
        df: The DataFrame to validate.
        required_vars: Set of required column names. Defaults to REQUIRED_VARIABLES.

    Returns:
        dict with 'status', 'missing_vars', and 'timestamp'.
    """
    if required_vars is None:
        required_vars = REQUIRED_VARIABLES

    missing_vars = list(required_vars - set(df.columns))
    status = "pass" if len(missing_vars) == 0 else "fail"
    timestamp = datetime.utcnow().isoformat()

    return {
        "status": status,
        "missing_vars": missing_vars,
        "timestamp": timestamp
    }

def validate_raw_directory(raw_dir: Path) -> dict:
    """
    Scans the raw data directory for CSV/Parquet files and validates them.
    If multiple files exist, it validates the first one found (assuming single dataset per run).
    If no file is found, it triggers synthetic generation logic by returning a 'fail' status.

    Args:
        raw_dir: Path to the data/raw directory.

    Returns:
        dict with validation status and details.
    """
    if not raw_dir.exists():
        return {
            "status": "fail",
            "missing_vars": ["Directory data/raw not found"],
            "timestamp": datetime.utcnow().isoformat(),
            "error": "Directory missing"
        }

    # Look for CSV or Parquet files
    files = list(raw_dir.glob("*.csv")) + list(raw_dir.glob("*.parquet"))
    
    if not files:
        return {
            "status": "fail",
            "missing_vars": ["No data files found in data/raw"],
            "timestamp": datetime.utcnow().isoformat(),
            "error": "No data files"
        }

    # Select the first file (assuming single dataset for this pipeline run)
    target_file = files[0]
    logger = get_logger(__name__)
    logger.info(f"Validating data file: {target_file}")

    try:
        if target_file.suffix == '.csv':
            df = pd.read_csv(target_file)
        elif target_file.suffix == '.parquet':
            df = pd.read_parquet(target_file)
        else:
            return {
                "status": "fail",
                "missing_vars": [f"Unsupported file format: {target_file.suffix}"],
                "timestamp": datetime.utcnow().isoformat(),
                "error": "Unsupported format"
            }
        
        return validate_raw_data_variables(df)

    except Exception as e:
        logger.error(f"Failed to read or validate {target_file}: {e}")
        return {
            "status": "fail",
            "missing_vars": [str(e)],
            "timestamp": datetime.utcnow().isoformat(),
            "error": "Read error"
        }

def run_validation():
    """
    Main entry point for the validation script.
    Reads from data/raw, validates variables, and writes to data/processed/pre_imputation_validation.json.
    If validation fails, it logs the failure and triggers the synthetic data generation path
    by calling check_fallback_trigger from download.py.
    """
    config = get_config()
    raw_dir = config.get_path('raw_data')
    output_path = config.get_path('pre_imputation_validation')
    
    logger = get_logger(__name__)
    log_execution_start(logger, "T013a Pre-Imputation Variable Check")

    logger.info(f"Checking raw data directory: {raw_dir}")
    result = validate_raw_directory(raw_dir)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write the validation result to JSON
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Validation result written to {output_path}")

    if result['status'] == 'fail':
        logger.warning("Validation failed. Triggering synthetic data generation fallback.")
        # Import here to avoid circular dependency issues at module load time
        from data.download import check_fallback_trigger
        try:
            check_fallback_trigger(reason="missing_variables", missing_vars=result.get('missing_vars', []))
        except Exception as e:
            logger.error(f"Failed to trigger fallback: {e}")
            raise
    else:
        logger.info("Validation passed. Proceeding to imputation.")

    log_execution_end(logger, "T013a Pre-Imputation Variable Check")
    return result

if __name__ == "__main__":
    run_validation()
