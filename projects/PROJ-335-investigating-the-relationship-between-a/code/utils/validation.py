"""
Validation utilities for EEG and Behavioral data.
Implements T005 and supports T016.
"""
import sys
import os
import logging
from typing import List, Set, Dict, Any, Optional, Union
from pathlib import Path
import numpy as np
import pandas as pd

# Error Codes as per FR-006
ERR_FR006_MISSING_BEHAVIORAL = 106
ERR_FR006_MISSING_CHANNELS = 105
ERR_GENERIC_VALIDATION = 100

def log_error(logger, message, error_code):
    """Log error and exit."""
    logger.error(f"ERROR [Code {error_code}]: {message}")
    sys.exit(error_code)

def validate_file_exists(path, logger):
    """Check if a file exists."""
    if not Path(path).exists():
        log_error(logger, f"File not found: {path}", ERR_GENERIC_VALIDATION)
    return True

def validate_dataframe_not_empty(df, logger):
    """Check if dataframe has rows."""
    if df.empty:
        log_error(logger, "Dataframe is empty.", ERR_GENERIC_VALIDATION)
    return True

def validate_eeg_channels(df, required_channels, logger):
    """
    Validate that required EEG channels are present.
    """
    missing = set(required_channels) - set(df.columns)
    if missing:
        log_error(logger, f"Missing required EEG channels: {missing}", ERR_FR006_MISSING_CHANNELS)
    return True

def validate_behavioral_metrics(df, required_cols, logger):
    """
    Validate that required behavioral columns (k-scores/d') are present.
    """
    missing = set(required_cols) - set(df.columns)
    if missing:
        log_error(logger, f"Missing required behavioral metrics: {missing}", ERR_FR006_MISSING_BEHAVIORAL)
    return True

def exit_on_validation_failure(df, required_cols, error_code, error_msg):
    """
    T016 Integration: Wrapper to invoke validation and exit on failure.
    Checks for required columns and exits with specific error code.
    """
    logger = logging.getLogger(__name__)
    
    if df is None:
        log_error(logger, "Dataframe is None.", error_code)
    
    if not isinstance(df, pd.DataFrame):
        log_error(logger, "Input is not a pandas DataFrame.", error_code)

    # Check for missing columns
    missing = set(required_cols) - set(df.columns)
    if missing:
        # Log the specific error message requested in T016
        logger.error(f"{error_msg} Missing: {missing}")
        sys.exit(error_code)
    
    return True

def load_and_validate_csv(file_path, required_cols, logger):
    """Load CSV and validate columns in one step."""
    validate_file_exists(file_path, logger)
    df = pd.read_csv(file_path)
    validate_behavioral_metrics(df, required_cols, logger)
    return df

def validate_dataset(dataset_path, logger):
    """High level dataset validation."""
    validate_file_exists(dataset_path, logger)
    return True

def main():
    """Simple CLI for validation testing."""
    import argparse
    parser = argparse.ArgumentParser(description="Validate data files")
    parser.add_argument("--file", type=str, required=True, help="Path to CSV")
    parser.add_argument("--cols", type=str, nargs="+", default=[], help="Required columns")
    args = parser.parse_args()
    
    logger = logging.getLogger("validation_cli")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    logger.addHandler(handler)
    
    if args.cols:
        load_and_validate_csv(args.file, args.cols, logger)
        print("Validation passed.")
    else:
        print("No columns specified to validate.")

if __name__ == "__main__":
    main()