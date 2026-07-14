"""
Validation step for the Neural Narrative Networks pipeline.

This module implements strict validation of downloaded and processed data.
It halts execution with specific error messages if data is corrupted, incomplete,
or fails schema validation.
"""
import os
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

import numpy as np
import pandas as pd

from config import get_config
from utils.logging_config import get_logger, error, info, warning, critical
from utils.schema_validation import validate_neural_data, validate_text_data, validate_rsa_output
from utils.checksums import verify_file_integrity, load_state_file

logger = get_logger(__name__)

# Error codes as defined in logging_config
ERR_CORRUPT_HEADER = "E001"
ERR_MISSING_FILE = "E002"
ERR_INVALID_SCHEMA = "E003"
ERR_INCOMPLETE_DATA = "E004"
ERR_CHECKSUM_MISMATCH = "E005"

def check_file_exists(file_path: Path) -> bool:
    """Check if a required file exists."""
    if not file_path.exists():
        error(f"{ERR_MISSING_FILE}: Required file not found: {file_path}")
        return False
    return True

def check_file_not_empty(file_path: Path) -> bool:
    """Check if a file is not empty."""
    if file_path.stat().st_size == 0:
        error(f"{ERR_CORRUPT_HEADER}: File is empty: {file_path}")
        return False
    return True

def validate_neural_roi_csv(file_path: Path) -> bool:
    """
    Validate the ROI timecourses CSV file.
    
    Expected format: CSV with columns for subject_id, roi, and timepoints.
    Checks for:
    - File existence
    - Non-empty file
    - Correct column structure
    - Valid data types
    - No NaN values in critical columns
    """
    if not check_file_exists(file_path):
        return False
    
    if not check_file_not_empty(file_path):
        return False

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        error(f"{ERR_CORRUPT_HEADER}: Failed to parse CSV {file_path}: {str(e)}")
        return False

    # Check required columns
    required_cols = ['subject_id', 'roi', 'mean_signal']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        error(f"{ERR_INCOMPLETE_DATA}: Missing required columns in {file_path}: {missing_cols}")
        return False

    # Check for NaN in critical columns
    if df['subject_id'].isna().any():
        error(f"{ERR_CORRUPT_HEADER}: Found NaN values in 'subject_id' column in {file_path}")
        return False
    
    if df['roi'].isna().any():
        error(f"{ERR_CORRUPT_HEADER}: Found NaN values in 'roi' column in {file_path}")
        return False

    # Validate ROI values
    valid_rois = {'L_Hippocampus', 'R_Hippocampus', 'L_DLPFC', 'R_DLPFC'}
    unique_rois = set(df['roi'].unique())
    invalid_rois = unique_rois - valid_rois
    
    if invalid_rois:
        error(f"{ERR_INCOMPLETE_DATA}: Invalid ROI values found in {file_path}: {invalid_rois}")
        return False

    # Check for at least one record
    if len(df) == 0:
        error(f"{ERR_INCOMPLETE_DATA}: No data records found in {file_path}")
        return False

    info(f"ROI timecourses validation passed: {len(df)} records in {file_path}")
    return True

def validate_event_averages_csv(file_path: Path) -> bool:
    """
    Validate the event averages CSV file.
    
    Expected format: CSV with columns: subject_id, event_id, roi, mean_signal.
    """
    if not check_file_exists(file_path):
        return False
    
    if not check_file_not_empty(file_path):
        return False

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        error(f"{ERR_CORRUPT_HEADER}: Failed to parse CSV {file_path}: {str(e)}")
        return False

    required_cols = ['subject_id', 'event_id', 'roi', 'mean_signal']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        error(f"{ERR_INCOMPLETE_DATA}: Missing required columns in {file_path}: {missing_cols}")
        return False

    # Check for NaN in critical columns
    critical_cols = ['subject_id', 'event_id', 'roi']
    for col in critical_cols:
        if df[col].isna().any():
            error(f"{ERR_CORRUPT_HEADER}: Found NaN values in '{col}' column in {file_path}")
            return False

    if len(df) == 0:
        error(f"{ERR_INCOMPLETE_DATA}: No data records found in {file_path}")
        return False

    info(f"Event averages validation passed: {len(df)} records in {file_path}")
    return True

def validate_text_jsonl(file_path: Path) -> bool:
    """
    Validate the ROCStories JSONL file.
    
    Checks for:
    - File existence
    - Valid JSON format for each line
    - Required fields in each record
    """
    if not check_file_exists(file_path):
        return False
    
    if not check_file_not_empty(file_path):
        return False

    required_fields = ['story_id', 'text']
    line_count = 0
    error_count = 0

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as e:
                    error(f"{ERR_CORRUPT_HEADER}: Invalid JSON on line {line_num} in {file_path}: {str(e)}")
                    error_count += 1
                    continue

                missing_fields = [field for field in required_fields if field not in record]
                if missing_fields:
                    error(f"{ERR_INCOMPLETE_DATA}: Missing fields on line {line_num} in {file_path}: {missing_fields}")
                    error_count += 1
                    continue

                if not isinstance(record.get('text'), str) or len(record['text'].strip()) == 0:
                    error(f"{ERR_INCOMPLETE_DATA}: Empty or invalid 'text' field on line {line_num} in {file_path}")
                    error_count += 1
                    continue

                line_count += 1

    except Exception as e:
        error(f"{ERR_CORRUPT_HEADER}: Failed to read file {file_path}: {str(e)}")
        return False

    if error_count > 0:
        error(f"{ERR_CORRUPT_HEADER}: {error_count} invalid records found in {file_path}")
        return False

    if line_count == 0:
        error(f"{ERR_INCOMPLETE_DATA}: No valid records found in {file_path}")
        return False

    info(f"Text data validation passed: {line_count} valid records in {file_path}")
    return True

def validate_checksums(file_paths: List[Path], state_file: Path) -> bool:
    """
    Validate file checksums against the state file.
    """
    if not check_file_exists(state_file):
        warning(f"State file not found: {state_file}. Skipping checksum validation.")
        return True

    try:
        state_data = load_state_file(state_file)
    except Exception as e:
        error(f"{ERR_CORRUPT_HEADER}: Failed to load state file {state_file}: {str(e)}")
        return False

    all_valid = True
    for file_path in file_paths:
        if not file_path.exists():
            continue  # Handled by other validators

        if file_path.name not in state_data:
            warning(f"No checksum recorded for {file_path.name} in state file")
            continue

        expected_checksum = state_data[file_path.name]
        is_valid = verify_file_integrity(file_path, expected_checksum)
        
        if not is_valid:
            error(f"{ERR_CHECKSUM_MISMATCH}: Checksum mismatch for {file_path}")
            all_valid = False
        else:
            info(f"Checksum valid for {file_path}")

    return all_valid

def run_full_validation(config: Dict[str, Any]) -> bool:
    """
    Run all validation checks on the pipeline data.
    
    This function performs a comprehensive validation of all data artifacts
    produced by the pipeline. If any check fails, it logs the specific error
    and returns False to halt the pipeline.
    
    Args:
        config: Configuration dictionary from get_config()
    
    Returns:
        bool: True if all validations pass, False otherwise
    """
    base_path = Path(config.get('data_dir', 'data'))
    state_file = Path(config.get('state_dir', 'state') / 'checksums.json')
    
    all_valid = True

    # Define paths to validate
    roi_timecourses_path = base_path / 'neural' / 'processed' / 'roi_timecourses.csv'
    event_averages_path = base_path / 'neural' / 'processed' / 'event_averages.csv'
    rocstories_path = base_path / 'text' / 'rocstories_sample.jsonl'

    # Validate ROI timecourses
    info("Validating ROI timecourses...")
    if not validate_neural_roi_csv(roi_timecourses_path):
        all_valid = False

    # Validate event averages
    info("Validating event averages...")
    if not validate_event_averages_csv(event_averages_path):
        all_valid = False

    # Validate text data
    info("Validating text data...")
    if not validate_text_jsonl(rocstories_path):
        all_valid = False

    # Validate checksums
    info("Validating checksums...")
    files_to_check = [roi_timecourses_path, event_averages_path, rocstories_path]
    if not validate_checksums(files_to_check, state_file):
        all_valid = False

    if all_valid:
        info("All validation checks passed.")
        return True
    else:
        critical("Validation failed. Halting pipeline.")
        return False

def main():
    """Main entry point for validation script."""
    config = get_config()
    success = run_full_validation(config)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()