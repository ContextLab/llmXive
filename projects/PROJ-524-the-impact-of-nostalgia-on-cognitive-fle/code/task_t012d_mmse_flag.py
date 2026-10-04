"""
Task T012d: MMSE Flag Implementation

Reads data/raw/raw_dataset.csv, checks if 'MMSE' column exists AND contains 
at least one non-null value. Writes has_mmse (True/False) to 
data/processed/mmse_flag.json.

If column missing OR all null, set has_mmse=False and log ERR_MMSE_MISSING.
Always raises DataNotFoundError if file is missing.
"""

import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any

# Import logging setup from utils
from utils import setup_logging, log_info, log_warning, log_error, get_timestamp

# Define a custom exception for data not found
class DataNotFoundError(Exception):
    """Raised when a required data file is missing."""
    pass

def load_raw_dataset(raw_path: Path) -> pd.DataFrame:
    """
    Load the raw dataset from the specified path.
    
    Args:
        raw_path: Path to the raw dataset CSV file.
        
    Returns:
        DataFrame containing the raw dataset.
        
    Raises:
        DataNotFoundError: If the file does not exist.
        ValueError: If the file is empty or cannot be read.
    """
    if not raw_path.exists():
        raise DataNotFoundError(f"Raw dataset file not found: {raw_path}")
    
    try:
        df = pd.read_csv(raw_path)
        if df.empty:
            raise ValueError(f"Raw dataset file is empty: {raw_path}")
        return df
    except Exception as e:
        raise ValueError(f"Failed to read raw dataset {raw_path}: {e}")

def validate_mmse_presence(df: pd.DataFrame) -> bool:
    """
    Check if 'MMSE' column exists and contains at least one non-null value.
    
    Args:
        df: DataFrame to check.
        
    Returns:
        True if MMSE column exists and has non-null values, False otherwise.
    """
    if 'MMSE' not in df.columns:
        return False
    
    # Check if there is at least one non-null value
    has_non_null = df['MMSE'].notna().any()
    return has_non_null

def save_mmse_flag(mmse_flag: bool, output_path: Path, logger: logging.Logger) -> None:
    """
    Save the MMSE flag to a JSON file.
    
    Args:
        mmse_flag: Boolean indicating if MMSE data is present.
        output_path: Path to the output JSON file.
        logger: Logger instance.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    result = {
        "has_mmse": mmse_flag,
        "timestamp": get_timestamp()
    }
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    if mmse_flag:
        log_info(logger, "MMSE column found with non-null values.")
    else:
        log_warning(logger, "ERR_MMSE_MISSING: MMSE column missing or all null values.")

def main() -> int:
    """
    Main function to execute the MMSE flag task.
    
    Returns:
        0 on success, 1 on failure.
    """
    # Setup logging
    logger = setup_logging("task_t012d_mmse_flag")
    log_info(logger, f"Starting Task T012d: MMSE Flag Check at {get_timestamp()}")
    
    # Define paths
    # Assuming project root is two levels up from code/
    project_root = Path(__file__).resolve().parent.parent
    raw_dataset_path = project_root / "data" / "raw" / "raw_dataset.csv"
    output_path = project_root / "data" / "processed" / "mmse_flag.json"
    
    try:
        # Load raw dataset
        log_info(logger, f"Loading raw dataset from {raw_dataset_path}")
        df = load_raw_dataset(raw_dataset_path)
        log_info(logger, f"Loaded {len(df)} rows from raw dataset.")
        
        # Validate MMSE presence
        has_mmse = validate_mmse_presence(df)
        
        # Save result
        save_mmse_flag(has_mmse, output_path, logger)
        
        log_info(logger, f"Task T012d completed successfully. Output: {output_path}")
        return 0
        
    except DataNotFoundError as e:
        log_error(logger, f"DataNotFoundError: {e}")
        # Re-raise as per requirement: "Always raise DataNotFoundError if file is missing"
        raise
    except Exception as e:
        log_error(logger, f"Unexpected error during T012d execution: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
