import os
import sys
import logging
from pathlib import Path
from typing import List, Set

import pandas as pd

from utils.logger import get_logger
from utils.validators import load_schema, validate_dataframe_schema
from data.config import get_config

# Required variables for the social comparison study
REQUIRED_VARIABLES: Set[str] = {
    "avatar_condition",
    "pre_self_esteem",
    "post_self_esteem",
    "comparison_tendency"
}

logger = get_logger(__name__)


def validate_raw_data_variables(data_path: Path) -> bool:
    """
    Validates that a CSV file in data/raw contains ALL required variables.
    
    Args:
        data_path: Path to the CSV file to validate.
        
    Returns:
        bool: True if all required variables are present, False otherwise.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or not a valid CSV.
    """
    if not data_path.exists():
        raise FileNotFoundError(f"Raw data file not found: {data_path}")
    
    logger.info(f"Validating variables in {data_path}")
    
    try:
        df = pd.read_csv(data_path)
    except Exception as e:
        raise ValueError(f"Failed to read CSV file {data_path}: {e}")
    
    if df.empty:
        raise ValueError(f"Dataset at {data_path} is empty.")
    
    existing_columns = set(df.columns)
    missing_columns = REQUIRED_VARIABLES - existing_columns
    
    if missing_columns:
        logger.error(f"Missing required variables in {data_path}: {missing_columns}")
        logger.error(f"Found columns: {existing_columns}")
        return False
    
    logger.info(f"Validation passed for {data_path}. All {len(REQUIRED_VARIABLES)} required variables present.")
    return True


def validate_raw_directory(raw_dir: Path) -> bool:
    """
    Validates that the data/raw directory contains at least one valid CSV
    with all required variables.
    
    Args:
        raw_dir: Path to the data/raw directory.
        
    Returns:
        bool: True if validation passes for at least one file, False otherwise.
    """
    if not raw_dir.exists():
        logger.error(f"Raw data directory does not exist: {raw_dir}")
        return False
    
    csv_files = list(raw_dir.glob("*.csv"))
    
    if not csv_files:
        logger.error(f"No CSV files found in {raw_dir}")
        return False
    
    validation_passed = False
    
    for csv_file in csv_files:
        try:
            if validate_raw_data_variables(csv_file):
                validation_passed = True
                # If we found one valid file, we can proceed (or break if we only expect one)
                # For robustness, we log success and continue checking others if needed,
                # but strictly speaking, finding one valid dataset allows the pipeline to proceed.
                break
        except (FileNotFoundError, ValueError) as e:
            logger.warning(f"Skipping {csv_file} due to error: {e}")
            continue
    
    if not validation_passed:
        logger.error("No valid dataset found in data/raw with required variables.")
    
    return validation_passed


def run_validation() -> bool:
    """
    Entry point for the validation script.
    Loads config to find data/raw, validates the content, and returns status.
    
    Returns:
        bool: True if validation succeeds, False otherwise.
    """
    config = get_config()
    raw_dir = Path(config.data_raw_dir)
    
    logger.info("Starting raw data validation (T013)...")
    
    success = validate_raw_directory(raw_dir)
    
    if success:
        logger.info("T013 Validation: PASSED. Pipeline can proceed.")
    else:
        logger.error("T013 Validation: FAILED. Required variables missing.")
    
    return success


if __name__ == "__main__":
    success = run_validation()
    sys.exit(0 if success else 1)
