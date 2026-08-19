"""
Validation utilities for the EEG pipeline.
Implements T005 and T016: Validation logic for channels, behavioral metrics, and power.
"""
import sys
import os
import logging
from typing import List, Set, Dict, Any, Optional, Union
from pathlib import Path
import numpy as np
import json
import pandas as pd

from utils.logging_config import get_logger

logger = get_logger("validation")

def log_error(message: str):
    """Log an error message and exit."""
    logger.error(message)
    print(message, file=sys.stderr)

def validate_file_exists(file_path: Union[str, Path]):
    """Validate that a file exists."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return True

def validate_dataframe_not_empty(df: pd.DataFrame):
    """Validate that a dataframe is not empty."""
    if df.empty:
        raise ValueError("DataFrame is empty")
    return True

def validate_eeg_channels(channels: List[str], required: Set[str]):
    """
    Validate that required EEG channels are present.
    T016: Check for required channels (e.g., Fz, Pz) and halt if missing.
    """
    missing = required - set(channels)
    if missing:
        msg = f"CRITICAL: Missing required electrode data: {missing}"
        log_error(msg)
        sys.exit(1)
    return True

def validate_behavioral_metrics(metrics: Dict[str, Any], required_keys: Set[str]):
    """
    Validate that required behavioral metrics (k-scores, d') are present.
    T016: Exit with failure code if missing.
    """
    missing = required_keys - set(metrics.keys())
    if missing:
        msg = f"ERROR: Missing behavioral measures: {missing}"
        log_error(msg)
        sys.exit(1)
    return True

def exit_on_validation_failure(condition: bool, message: str):
    """Exit if condition is False."""
    if not condition:
        log_error(message)
        sys.exit(1)

def load_and_validate_csv(file_path: Union[str, Path], required_columns: List[str]):
    """Load a CSV and validate its columns."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    df = pd.read_csv(path)
    validate_dataframe_not_empty(df)
    
    missing_cols = set(required_columns) - set(df.columns)
    if missing_cols:
        msg = f"ERROR: Missing required columns in {path}: {missing_cols}"
        log_error(msg)
        sys.exit(1)
    
    return df

def validate_dataset(dataset: Dict[str, Any], required_fields: List[str]):
    """Validate a dataset dictionary for required fields."""
    missing = set(required_fields) - set(dataset.keys())
    if missing:
        msg = f"ERROR: Missing dataset fields: {missing}"
        log_error(msg)
        sys.exit(1)
    return True

def check_power_requirements(n_subjects: int, output_path: Path = Path("data/results/power_status.json")):
    """
    T017: Check power requirements.
    - If N < 30: Halt with 'INSUFFICIENT POWER'
    - If 30 <= N <= 52: Log warning, write power_status.json with status 'LIMITED', continue.
    - If N > 52: Proceed.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    status = "OK"
    message = ""
    
    if n_subjects < 30:
        message = "INSUFFICIENT POWER"
        logger.error(message)
        # Write status before exiting
        status_data = {"n_count": n_subjects, "status": "INSUFFICIENT", "message": message}
        with open(output_path, 'w') as f:
            json.dump(status_data, f, indent=2)
        sys.exit(1)
    elif n_subjects <= 52:
        message = "WARNING: Limited power (N between 30 and 52)"
        logger.warning(message)
        status_data = {"n_count": n_subjects, "status": "LIMITED", "message": message}
        with open(output_path, 'w') as f:
            json.dump(status_data, f, indent=2)
        status = "LIMITED"
    else:
        status_data = {"n_count": n_subjects, "status": "OK", "message": "Power sufficient"}
        with open(output_path, 'w') as f:
            json.dump(status_data, f, indent=2)
    
    return status

def main():
    """Main entry point for validation tests."""
    logger.info("Running validation tests...")
    # Example usage
    try:
        validate_eeg_channels(["Fz", "Pz", "Cz"], {"Fz", "Pz"})
        validate_behavioral_metrics({"k_score": 0.5, "d_prime": 1.2}, {"k_score", "d_prime"})
        check_power_requirements(40)
        logger.info("All validation tests passed.")
    except SystemExit as e:
        if e.code != 0:
            raise
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise

if __name__ == "__main__":
    main()
