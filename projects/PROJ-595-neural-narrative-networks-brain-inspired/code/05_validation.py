import os
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np

from config import get_config
from utils.logging_config import get_logger, info, error, warning, critical
from utils.schema_validation import validate_neural_data, validate_text_data, validate_rsa_output
from utils.checksums import verify_file_integrity, load_state_file

logger = get_logger(__name__)

# Error codes for specific failure modes
ERR_FILE_MISSING = "E101"
ERR_FILE_EMPTY = "E102"
ERR_SCHEMA_NEURAL = "E201"
ERR_SCHEMA_TEXT = "E202"
ERR_SCHEMA_RSA = "E203"
ERR_CHECKSUM_MISMATCH = "E301"
ERR_DATA_CORRUPT = "E401"

def check_file_exists(file_path: str) -> bool:
    """Check if a file exists at the given path."""
    path = Path(file_path)
    if not path.exists():
        error(f"{ERR_FILE_MISSING}: File not found: {file_path}")
        return False
    return True

def check_file_not_empty(file_path: str) -> bool:
    """Check if a file is not empty (has content)."""
    path = Path(file_path)
    if not check_file_exists(file_path):
        return False
    if path.stat().st_size == 0:
        error(f"{ERR_FILE_EMPTY}: File is empty: {file_path}")
        return False
    return True

def validate_neural_roi_csv(file_path: str) -> bool:
    """
    Validate neural ROI timecourses CSV file.
    Checks: existence, non-empty, schema validity via utils.schema_validation
    """
    if not check_file_exists(file_path):
        return False
    if not check_file_not_empty(file_path):
        return False

    # Attempt to load and validate structure
    try:
        # Basic structure check: header and at least one row
        with open(file_path, 'r') as f:
            header = f.readline().strip()
            if not header:
                error(f"{ERR_DATA_CORRUPT}: No header in {file_path}")
                return False
            first_row = f.readline()
            if not first_row:
                error(f"{ERR_DATA_CORRUPT}: No data rows in {file_path}")
                return False
    
        # Use schema validator if available
        if not validate_neural_data(file_path):
            error(f"{ERR_SCHEMA_NEURAL}: Schema validation failed for {file_path}")
            return False
        
        info(f"Neural ROI data validated successfully: {file_path}")
        return True
    except Exception as e:
        error(f"{ERR_DATA_CORRUPT}: Failed to read {file_path}: {str(e)}")
        return False

def validate_event_averages_csv(file_path: str) -> bool:
    """
    Validate event averages CSV file.
    Checks: existence, non-empty, required columns (subject_id, event_id, roi, mean_signal)
    """
    if not check_file_exists(file_path):
        return False
    if not check_file_not_empty(file_path):
        return False

    try:
        required_columns = {'subject_id', 'event_id', 'roi', 'mean_signal'}
        with open(file_path, 'r') as f:
            header_line = f.readline().strip()
            if not header_line:
                error(f"{ERR_DATA_CORRUPT}: No header in {file_path}")
                return False
            
            columns = set(col.strip() for col in header_line.split(','))
            if not required_columns.issubset(columns):
                missing = required_columns - columns
                error(f"{ERR_DATA_CORRUPT}: Missing required columns {missing} in {file_path}")
                return False
            
            # Check for at least one data row
            first_row = f.readline()
            if not first_row.strip():
                error(f"{ERR_DATA_CORRUPT}: No data rows in {file_path}")
                return False
        
        info(f"Event averages validated successfully: {file_path}")
        return True
    except Exception as e:
        error(f"{ERR_DATA_CORRUPT}: Failed to read {file_path}: {str(e)}")
        return False

def validate_text_jsonl(file_path: str) -> bool:
    """
    Validate text JSONL file (e.g., ROCStories sample).
    Checks: existence, non-empty, each line is valid JSON
    """
    if not check_file_exists(file_path):
        return False
    if not check_file_not_empty(file_path):
        return False

    try:
        valid_count = 0
        with open(file_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    json.loads(line)
                    valid_count += 1
                except json.JSONDecodeError as e:
                    error(f"{ERR_DATA_CORRUPT}: Invalid JSON on line {line_num} in {file_path}: {str(e)}")
                    return False
        
        if valid_count == 0:
            error(f"{ERR_DATA_CORRUPT}: No valid JSON lines found in {file_path}")
            return False

        # Use schema validator if available
        if not validate_text_data(file_path):
            error(f"{ERR_SCHEMA_TEXT}: Schema validation failed for {file_path}")
            return False

        info(f"Text data validated successfully ({valid_count} lines): {file_path}")
        return True
    except Exception as e:
        error(f"{ERR_DATA_CORRUPT}: Failed to read {file_path}: {str(e)}")
        return False

def validate_checksums(file_paths: List[str]) -> bool:
    """
    Validate file integrity using checksums from state file.
    """
    if not file_paths:
        return True

    state_file = Path(get_config().get('state_file', 'state/checksums.json'))
    if not state_file.exists():
        warning(f"State file not found: {state_file}. Skipping checksum validation.")
        return True

    try:
        state_data = load_state_file(state_file)
        all_valid = True

        for file_path in file_paths:
            if file_path not in state_data:
                warning(f"No checksum recorded for {file_path}. Skipping.")
                continue
            
            recorded_checksum = state_data[file_path]
            if not verify_file_integrity(file_path, recorded_checksum):
                error(f"{ERR_CHECKSUM_MISMATCH}: Checksum mismatch for {file_path}")
                all_valid = False
            else:
                info(f"Checksum valid: {file_path}")
        
        return all_valid
    except Exception as e:
        error(f"{ERR_DATA_CORRUPT}: Failed to validate checksums: {str(e)}")
        return False

def run_full_validation() -> bool:
    """
    Run full validation pipeline for all critical data artifacts.
    Halts execution if any validation fails.
    Returns True if all validations pass, False otherwise.
    """
    config = get_config()
    data_dir = Path(config.get('data_dir', 'data'))
    
    # Define critical files to validate
    critical_files = {
        'neural_roi': str(data_dir / 'neural' / 'processed' / 'roi_timecourses.csv'),
        'event_averages': str(data_dir / 'neural' / 'processed' / 'event_averages.csv'),
        'text_sample': str(data_dir / 'text' / 'rocstories_sample.jsonl'),
    }

    validation_results = {}
    has_error = False

    # Validate neural ROI timecourses
    info("Validating neural ROI timecourses...")
    if not validate_neural_roi_csv(critical_files['neural_roi']):
        critical(f"{ERR_DATA_CORRUPT}: Neural ROI timecourses validation failed. Halting pipeline.")
        has_error = True
    else:
        validation_results['neural_roi'] = True

    # Validate event averages
    info("Validating event averages...")
    if not validate_event_averages_csv(critical_files['event_averages']):
        critical(f"{ERR_DATA_CORRUPT}: Event averages validation failed. Halting pipeline.")
        has_error = True
    else:
        validation_results['event_averages'] = True

    # Validate text sample
    info("Validating text sample...")
    if not validate_text_jsonl(critical_files['text_sample']):
        critical(f"{ERR_DATA_CORRUPT}: Text sample validation failed. Halting pipeline.")
        has_error = True
    else:
        validation_results['text_sample'] = True

    # Validate checksums for all critical files
    info("Validating checksums...")
    if not validate_checksums(list(critical_files.values())):
        critical(f"{ERR_CHECKSUM_MISMATCH}: Checksum validation failed. Halting pipeline.")
        has_error = True

    if has_error:
        critical("VALIDATION FAILED: Pipeline halted due to data integrity issues.")
        return False
    else:
        info("VALIDATION PASSED: All data artifacts are valid.")
        return True

def main():
    """Entry point for validation script."""
    logger.info("Starting data validation pipeline for User Story 1...")
    success = run_full_validation()
    
    if not success:
        logger.critical("Validation failed. Exiting with error code 1.")
        sys.exit(1)
    else:
        logger.info("Validation completed successfully. Exiting with code 0.")
        sys.exit(0)

if __name__ == '__main__':
    main()