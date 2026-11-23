"""
T010i: VALIDATE DATA AVAILABILITY

Ensures that all required Phase 2 data artifacts exist and are non-empty.
This task acts as the final gate for Phase 2 before User Story 1 implementation.

Required Files:
- data/assets/kinetic_dataset.csv (from T010f)
- data/assets/reference_substructures.csv (from T010c)
- data/raw/qm9_subset.parquet (from T013)
"""

import os
import sys
import logging
import json
import pandas as pd
from typing import List, Tuple, Dict, Any

# Ensure project root is in path for imports if running as script
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config import get_config, ensure_directories
from utils.logging_utils import setup_logging, log_metric, get_logger

# Define the expected files relative to project root
REQUIRED_FILES = [
    "data/assets/kinetic_dataset.csv",
    "data/assets/reference_substructures.csv",
    "data/raw/qm9_subset.parquet"
]

def setup_script_logging():
    """Initialize logging for the script."""
    logger = setup_logging("validate_data_availability")
    return logger

def check_file_exists(filepath: str) -> bool:
    """Check if a file exists."""
    return os.path.isfile(filepath)

def check_file_non_empty(filepath: str) -> Tuple[bool, int]:
    """
    Check if a file is non-empty.
    For CSV/Parquet, we check if it has rows. For others, we check file size.
    Returns (is_non_empty, size_or_rows).
    """
    if not os.path.isfile(filepath):
        return False, 0

    file_size = os.path.getsize(filepath)
    if file_size == 0:
        return False, 0

    # Try to read as pandas to check for rows if it's a data file
    try:
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath, nrows=1) # Read just header/one row to check
            # If we get here, it's not empty. Check row count properly.
            df = pd.read_csv(filepath)
            return len(df) > 0, len(df)
        elif filepath.endswith('.parquet'):
            df = pd.read_parquet(filepath)
            return len(df) > 0, len(df)
        else:
            # Generic file size check
            return file_size > 0, file_size
    except Exception as e:
        logging.getLogger(__name__).warning(f"Could not parse {filepath} as data: {e}. Checking size only.")
        return file_size > 0, file_size

def validate_data_availability(logger: logging.Logger) -> Dict[str, Any]:
    """
    Validate that all required files exist and are non-empty.
    Returns a report dictionary.
    """
    results = {}
    all_valid = True
    missing_files = []
    empty_files = []

    for filepath in REQUIRED_FILES:
        full_path = os.path.join(project_root, filepath)
        logger.info(f"Checking: {filepath}")

        exists = check_file_exists(full_path)
        if not exists:
            missing_files.append(filepath)
            results[filepath] = {"exists": False, "valid": False, "reason": "File not found"}
            all_valid = False
            continue

        is_non_empty, metric = check_file_non_empty(full_path)
        if not is_non_empty:
            empty_files.append(filepath)
            results[filepath] = {"exists": True, "valid": False, "reason": "File is empty", "metric": metric}
            all_valid = False
        else:
            results[filepath] = {"exists": True, "valid": True, "metric": metric}
            logger.info(f"  -> Valid: {metric} rows/bytes")

    report = {
        "task_id": "T010i",
        "status": "PASSED" if all_valid else "FAILED",
        "missing_files": missing_files,
        "empty_files": empty_files,
        "details": results,
        "timestamp": str(pd.Timestamp.now())
    }

    # Write report to artifacts
    artifacts_dir = os.path.join(project_root, "artifacts")
    ensure_directories([artifacts_dir])
    report_path = os.path.join(artifacts_dir, "data_availability_report.json")

    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Validation report written to: {report_path}")

    return report

def main():
    """Main entry point."""
    logger = setup_script_logging()
    logger.info("Starting T010i: Validate Data Availability")

    try:
        report = validate_data_availability(logger)
        
        if report["status"] == "FAILED":
            logger.error("VALIDATION FAILED. Missing or empty files found.")
            if report["missing_files"]:
                logger.error(f"Missing: {report['missing_files']}")
            if report["empty_files"]:
                logger.error(f"Empty: {report['empty_files']}")
            sys.exit(1)
        else:
            logger.info("VALIDATION PASSED. All required data artifacts are present and non-empty.")
            sys.exit(0)

    except Exception as e:
        logger.critical(f"Unexpected error during validation: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()