import os
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

import numpy as np

from config import get_config
from utils.logging_config import get_logger, info, error, warning, critical
from utils.schema_validation import validate_neural_data, validate_text_data, validate_rsa_output
from utils.checksums import load_state_file, verify_file_integrity

logger = get_logger(__name__)

# Error codes mapping to specific failure modes
ERRORS = {
    "E001": "Data corruption detected: file checksum mismatch.",
    "E002": "Incomplete data: expected file missing or zero bytes.",
    "E003": "Schema violation: neural data structure invalid.",
    "E004": "Schema violation: text data structure invalid.",
    "E005": "Schema violation: RSA output structure invalid.",
    "E006": "Data integrity failure: column count mismatch in CSV.",
    "E007": "Data integrity failure: unexpected NaN/Inf values in neural data.",
    "E008": "Configuration error: required environment variables missing.",
    "E009": "Pipeline halt: critical data dependency missing.",
    "E010": "Data format error: JSONL line parsing failed.",
}

def check_file_exists(file_path: str, description: str) -> bool:
    """Check if a file exists. Returns True if found, logs error and returns False otherwise."""
    path = Path(file_path)
    if not path.exists():
        error(f"{description} not found at: {file_path}")
        error(f"Error Code: E009 - {ERRORS['E009']}")
        return False
    info(f"Verified existence of {description}: {file_path}")
    return True

def check_file_not_empty(file_path: str, description: str) -> bool:
    """Check if a file is not empty (size > 0). Returns True if valid, logs error otherwise."""
    path = Path(file_path)
    if not path.exists():
        return False  # Handled by check_file_exists
    
    if path.stat().st_size == 0:
        error(f"{description} is empty at: {file_path}")
        error(f"Error Code: E002 - {ERRORS['E002']}")
        return False
    
    info(f"Verified non-empty status of {description}: {file_path}")
    return True

def validate_neural_roi_csv(file_path: str) -> bool:
    """
    Validate the structure and integrity of the ROI timecourses CSV.
    Checks:
    1. File exists and is not empty.
    2. Header matches expected columns: subject_id, roi, timepoint, value (or similar).
    3. No NaN or Inf values in the numeric 'value' column.
    """
    if not check_file_exists(file_path, "Neural ROI CSV"):
        return False
    if not check_file_not_empty(file_path, "Neural ROI CSV"):
        return False

    try:
        # Attempt to load a sample to verify structure
        # We use numpy to avoid pandas dependency if not strictly needed, 
        # but pandas is in requirements so we can use it for robustness if desired.
        # Given the constraints, let's use a simple CSV reader logic or numpy.
        import csv
        with open(file_path, 'r') as f:
            reader = csv.reader(f)
            header = next(reader)
            
            # Expected header based on T013/T017 context: subject_id, roi, timepoint, value
            # Or subject_id, roi, mean_signal (for event averages). 
            # For T016 generic validation, we check for numeric columns.
            if len(header) < 3:
                error(f"Neural ROI CSV header too short: {header}")
                error(f"Error Code: E006 - {ERRORS['E006']}")
                return False

            # Check for NaN/Inf in the last column (assuming numeric values)
            numeric_col_idx = -1 
            # Heuristic: find the last column that looks numeric in the first data row
            first_row = next(reader)
            for i, val in enumerate(first_row):
                try:
                    float(val)
                    numeric_col_idx = i
                    break
                except ValueError:
                    continue
            
            if numeric_col_idx == -1:
                error("Could not identify numeric data column in Neural ROI CSV.")
                error(f"Error Code: E007 - {ERRORS['E007']}")
                return False

            # Validate remaining rows for NaN/Inf
            for row_num, row in enumerate(reader, start=2):
                if len(row) != len(header):
                    error(f"Row {row_num} column count mismatch: {len(row)} vs {len(header)}")
                    error(f"Error Code: E006 - {ERRORS['E006']}")
                    return False
                
                try:
                    val = float(row[numeric_col_idx])
                    if np.isnan(val) or np.isinf(val):
                        error(f"Found NaN/Inf in row {row_num}, column {numeric_col_idx}")
                        error(f"Error Code: E007 - {ERRORS['E007']}")
                        return False
                except ValueError:
                    # If the numeric column contains non-numeric data where expected
                    error(f"Non-numeric value in numeric column at row {row_num}")
                    error(f"Error Code: E007 - {ERRORS['E007']}")
                    return False

        info("Neural ROI CSV validation passed.")
        return True

    except Exception as e:
        error(f"Error reading Neural ROI CSV: {str(e)}")
        error(f"Error Code: E003 - {ERRORS['E003']}")
        return False

def validate_event_averages_csv(file_path: str) -> bool:
    """
    Validate the event averages CSV.
    Expected columns: subject_id, event_id, roi, mean_signal.
    """
    if not check_file_exists(file_path, "Event Averages CSV"):
        return False
    if not check_file_not_empty(file_path, "Event Averages CSV"):
        return False

    try:
        import csv
        with open(file_path, 'r') as f:
            reader = csv.reader(f)
            header = next(reader)
            
            expected_headers = ['subject_id', 'event_id', 'roi', 'mean_signal']
            if header != expected_headers:
                error(f"Event Averages CSV header mismatch. Expected: {expected_headers}, Got: {header}")
                error(f"Error Code: E006 - {ERRORS['E006']}")
                return False

            for row_num, row in enumerate(reader, start=2):
                if len(row) != 4:
                    error(f"Row {row_num} column count mismatch in Event Averages CSV.")
                    error(f"Error Code: E006 - {ERRORS['E006']}")
                    return False
                
                # Validate mean_signal is numeric and not NaN/Inf
                try:
                    val = float(row[3])
                    if np.isnan(val) or np.isinf(val):
                        error(f"Invalid mean_signal (NaN/Inf) in row {row_num}")
                        error(f"Error Code: E007 - {ERRORS['E007']}")
                        return False
                except ValueError:
                    error(f"Non-numeric mean_signal in row {row_num}")
                    error(f"Error Code: E007 - {ERRORS['E007']}")
                    return False

        info("Event Averages CSV validation passed.")
        return True

    except Exception as e:
        error(f"Error reading Event Averages CSV: {str(e)}")
        error(f"Error Code: E003 - {ERRORS['E003']}")
        return False

def validate_text_jsonl(file_path: str) -> bool:
    """
    Validate the text JSONL file.
    Checks:
    1. File exists and is not empty.
    2. Each line is valid JSON.
    """
    if not check_file_exists(file_path, "Text JSONL"):
        return False
    if not check_file_not_empty(file_path, "Text JSONL"):
        return False

    try:
        line_count = 0
        with open(file_path, 'r') as f:
            for line_num, line in enumerate(f, start=1):
                line_count += 1
                stripped = line.strip()
                if not stripped:
                    continue  # Skip empty lines if any
                
                try:
                    json.loads(stripped)
                except json.JSONDecodeError as e:
                    error(f"Invalid JSON at line {line_num} in {file_path}: {str(e)}")
                    error(f"Error Code: E010 - {ERRORS['E010']}")
                    return False

        if line_count == 0:
            error(f"Text JSONL file {file_path} contains no valid JSON lines.")
            error(f"Error Code: E002 - {ERRORS['E002']}")
            return False

        info(f"Text JSONL validation passed. {line_count} lines.")
        return True

    except Exception as e:
        error(f"Error reading Text JSONL: {str(e)}")
        error(f"Error Code: E004 - {ERRORS['E004']}")
        return False

def validate_checksums() -> bool:
    """
    Verify checksums against the state file.
    Returns True if all files match, False otherwise.
    """
    state_file_path = Path("state/checksums.json")
    if not state_file_path.exists():
        warning("State file not found. Skipping checksum validation.")
        return True

    try:
        state = load_state_file(state_file_path)
        if not state or 'checksums' not in state:
            error("Invalid state file format.")
            error(f"Error Code: E001 - {ERRORS['E001']}")
            return False

        failed_files = []
        for file_path, expected_hash in state['checksums'].items():
            if not Path(file_path).exists():
                failed_files.append(f"{file_path} (missing)")
                continue
            
            if not verify_file_integrity(file_path, expected_hash):
                failed_files.append(f"{file_path} (mismatch)")

        if failed_files:
            error(f"Checksum verification failed for {len(failed_files)} files:")
            for f in failed_files:
                error(f"  - {f}")
            error(f"Error Code: E001 - {ERRORS['E001']}")
            return False

        info("Checksum validation passed.")
        return True

    except Exception as e:
        error(f"Error during checksum validation: {str(e)}")
        error(f"Error Code: E001 - {ERRORS['E001']}")
        return False

def run_full_validation() -> bool:
    """
    Run all validation steps. Halts execution (returns False) if any critical check fails.
    Returns True only if all checks pass.
    """
    logger.info("Starting full pipeline validation...")
    config = get_config()
    
    all_passed = True

    # 1. Validate Neural Data (ROI Timecourses)
    roi_path = Path("data/neural/processed/roi_timecourses.csv")
    if not validate_neural_roi_csv(str(roi_path)):
        all_passed = False

    # 2. Validate Event Averages
    event_path = Path("data/neural/processed/event_averages.csv")
    if event_path.exists():
        if not validate_event_averages_csv(str(event_path)):
            all_passed = False

    # 3. Validate Text Data (ROCStories)
    text_path = Path("data/text/rocstories_sample.jsonl")
    if text_path.exists():
        if not validate_text_jsonl(str(text_path)):
            all_passed = False
    else:
        warning("Text data file not found. Skipping text validation.")

    # 4. Validate Checksums
    if not validate_checksums():
        all_passed = False

    if all_passed:
        logger.info("All validation checks PASSED.")
        return True
    else:
        logger.critical("VALIDATION FAILED. Pipeline halted due to data integrity issues.")
        return False

def main():
    """Entry point for validation script."""
    success = run_full_validation()
    if not success:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()