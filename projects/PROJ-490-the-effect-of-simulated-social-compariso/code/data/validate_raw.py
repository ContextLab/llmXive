"""
Validation module for ensuring data/raw contains all required variables.
Implements FR-009: Verify presence of avatar_condition, pre_self_esteem,
post_self_esteem, and comparison_tendency before proceeding.
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Set

import pandas as pd

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logger import get_logger, log_execution_start, log_execution_end
from utils.validators import validate_dataframe_schema
from data.config import get_config

REQUIRED_VARIABLES: Set[str] = {
    "avatar_condition",
    "pre_self_esteem",
    "post_self_esteem",
    "comparison_tendency"
}

logger = get_logger(__name__)


def validate_raw_data_variables(data_path: Path) -> bool:
    """
    Validates that the CSV file at data_path contains all required variables.
    
    Args:
        data_path: Path to the CSV file in data/raw to validate.
        
    Returns:
        bool: True if all required variables are present, False otherwise.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is not a valid CSV or is empty.
    """
    if not data_path.exists():
        logger.error(f"File not found: {data_path}")
        raise FileNotFoundError(f"File not found: {data_path}")
    
    try:
        df = pd.read_csv(data_path)
    except Exception as e:
        logger.error(f"Failed to read CSV {data_path}: {e}")
        raise ValueError(f"Invalid CSV file: {data_path}") from e
    
    if df.empty:
        logger.error(f"Dataset at {data_path} is empty.")
        raise ValueError(f"Dataset at {data_path} is empty.")
    
    available_columns = set(df.columns)
    missing_columns = REQUIRED_VARIABLES - available_columns
    
    if missing_columns:
        logger.error(f"Missing required variables in {data_path}: {missing_columns}")
        logger.error(f"Available columns: {available_columns}")
        return False
    
    logger.info(f"Validation successful for {data_path}. All required variables present.")
    return True


def validate_raw_directory(raw_dir: Path) -> bool:
    """
    Validates that all CSV files in the raw directory contain required variables.
    Stops at the first valid file found and returns True, or returns False if
    no valid file is found.
    
    Args:
        raw_dir: Path to the data/raw directory.
        
    Returns:
        bool: True if at least one valid file is found, False otherwise.
    """
    if not raw_dir.exists():
        logger.error(f"Directory not found: {raw_dir}")
        return False
    
    csv_files = list(raw_dir.glob("*.csv"))
    
    if not csv_files:
        logger.warning(f"No CSV files found in {raw_dir}")
        return False
    
    valid_count = 0
    for csv_file in csv_files:
        try:
            if validate_raw_data_variables(csv_file):
                valid_count += 1
                # We only need one valid file to proceed
                return True
        except (FileNotFoundError, ValueError) as e:
            logger.warning(f"Skipping {csv_file} due to error: {e}")
            continue
    
    logger.error(f"No valid CSV files found in {raw_dir} containing all required variables.")
    return False


def run_validation() -> bool:
    """
    Entry point for the validation script. Loads config, checks the raw data
    directory, and returns the validation status.
    
    Returns:
        bool: True if validation passes, False otherwise.
    """
    log_execution_start(logger, "validate_raw_data")
    
    config = get_config()
    raw_dir = config.get("paths", {}).get("raw_data_dir")
    
    if not raw_dir:
        # Fallback to default if not in config
        raw_dir = Path(project_root) / "data" / "raw"
    
    logger.info(f"Validating raw data directory: {raw_dir}")
    
    success = validate_raw_directory(Path(raw_dir))
    
    log_execution_end(logger, "validate_raw_data", success=success)
    
    if not success:
        logger.error("Validation failed. Please ensure data/raw contains CSV files with all required variables.")
        return False
    
    logger.info("Validation passed. Pipeline can proceed.")
    return True


if __name__ == "__main__":
    success = run_validation()
    sys.exit(0 if success else 1)
