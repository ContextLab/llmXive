"""
Task T012d: MMSE Flag Implementation

Logic:
1. Read `data/raw/raw_dataset.csv`.
2. Check if 'MMSE' column exists AND contains at least one non-null value.
3. If column missing OR all null, set `has_mmse=False` and log `ERR_MMSE_MISSING` WITHOUT raising an error.
4. Write `has_mmse` (True/False) to `data/processed/mmse_flag.json`.
"""

import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any

# Import shared utilities from existing API
from utils import setup_logging, log_info, log_warning, log_error, get_timestamp
from config import get_config, get_config_value

# Configure logging
logger = setup_logging()

class DataNotFoundError(Exception):
    """Raised when a required data file is missing."""
    pass

def get_config_paths() -> Dict[str, Path]:
    """Retrieve project paths from config."""
    config = get_config()
    return {
        'root': Path(config['paths']['root']),
        'raw': Path(config['paths']['raw']),
        'processed': Path(config['paths']['processed'])
    }

def load_raw_dataset(raw_dir: Path) -> pd.DataFrame:
    """
    Load the raw dataset from disk.
    
    Args:
        raw_dir: Path to the raw data directory.
        
    Returns:
        DataFrame containing the raw dataset.
        
    Raises:
        DataNotFoundError: If the raw dataset file does not exist.
    """
    filepath = raw_dir / "raw_dataset.csv"
    if not filepath.exists():
        raise DataNotFoundError(f"Raw dataset not found at {filepath}")
    
    logger.info(f"Loading raw dataset from {filepath}")
    df = pd.read_csv(filepath)
    return df

def validate_mmse_presence(df: pd.DataFrame) -> bool:
    """
    Check if 'MMSE' column exists and contains at least one non-null value.
    
    Args:
        df: The raw dataset DataFrame.
        
    Returns:
        True if 'MMSE' exists and has non-null values, False otherwise.
    """
    if 'MMSE' not in df.columns:
        log_warning("ERR_MMSE_MISSING: Column 'MMSE' not found in dataset.")
        return False
    
    if df['MMSE'].isnull().all():
        log_warning("ERR_MMSE_MISSING: Column 'MMSE' exists but contains only null values.")
        return False
    
    non_null_count = df['MMSE'].notnull().sum()
    log_info(f"MMSE column found with {non_null_count} non-null values.")
    return True

def save_mmse_flag(has_mmse: bool, processed_dir: Path) -> None:
    """
    Write the MMSE flag to a JSON file.
    
    Args:
        has_mmse: Boolean flag indicating MMSE availability.
        processed_dir: Path to the processed data directory.
    """
    filepath = processed_dir / "mmse_flag.json"
    data = {
        "has_mmse": has_mmse,
        "timestamp": get_timestamp()
    }
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    
    log_info(f"MMSE flag saved to {filepath}: has_mmse={has_mmse}")

def main() -> int:
    """
    Main entry point for Task T012d.
    
    Returns:
        0 on success, 1 on failure.
    """
    try:
        paths = get_config_paths()
        raw_dir = paths['raw']
        processed_dir = paths['processed']
        
        # Ensure processed directory exists
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Load raw dataset
        df = load_raw_dataset(raw_dir)
        
        # Validate MMSE presence
        has_mmse = validate_mmse_presence(df)
        
        # Save result
        save_mmse_flag(has_mmse, processed_dir)
        
        return 0
        
    except DataNotFoundError as e:
        log_error(str(e))
        return 1
    except Exception as e:
        log_error(f"Unexpected error during MMSE flag generation: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
