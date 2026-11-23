"""
Automated ingestion script for manual audit sample.

Polls for the human-labeled audit sample file, validates its schema,
and exits with appropriate status codes.
"""
import csv
import logging
import time
import sys
from pathlib import Path
from typing import List, Set, Tuple, Any

# Import local utilities matching the project API surface
from code.utils.logger import get_logger
from code.utils.config import set_global_seed

# Constants
AUDIT_FILE_PATH = Path("docs/reports/audit_sample_labeled.csv")
REQUIRED_COLUMNS = {"pr_id", "human_label"}
ALLOWED_LABELS: Set[str] = {"LLM", "Human"}
POLL_INTERVAL_SECONDS = 10
MAX_RETRIES = 60  # Wait up to 10 minutes (60 * 10s) before giving up


def validate_schema(file_path: Path) -> Tuple[bool, List[str]]:
    """
    Validates the CSV file schema.

    Checks:
    1. File exists.
    2. Contains required columns: 'pr_id', 'human_label'.
    3. No null values in required columns.
    4. 'human_label' values are strictly 'LLM' or 'Human'.

    Returns:
        Tuple[bool, List[str]]: (is_valid, list_of_error_messages)
    """
    errors: List[str] = []

    if not file_path.exists():
        errors.append(f"File not found: {file_path}")
        return False, errors

    try:
        with open(file_path, mode="r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)

            # Check headers
            if reader.fieldnames is None:
                errors.append("CSV file is empty or has no headers.")
                return False, errors

            header_set = set(reader.fieldnames)
            missing_cols = REQUIRED_COLUMNS - header_set
            if missing_cols:
                errors.append(f"Missing required columns: {missing_cols}")
                return False, errors

            # Check rows
            row_count = 0
            for row_num, row in enumerate(reader, start=2):  # Start at 2 (1-based + header)
                row_count += 1

                # Check for nulls in required columns
                for col in REQUIRED_COLUMNS:
                    val = row.get(col)
                    if val is None or val.strip() == "":
                        errors.append(f"Row {row_num}: Null value in required column '{col}'")
                        # We continue to collect errors but could break early if strict

                # Check allowed values for human_label
                label_val = row.get("human_label")
                if label_val is not None and label_val.strip() != "":
                    if label_val.strip() not in ALLOWED_LABELS:
                        errors.append(f"Row {row_num}: Invalid label '{label_val}'. Allowed: {ALLOWED_LABELS}")

            if row_count == 0:
                errors.append("CSV file contains no data rows.")
                return False, errors

    except csv.Error as e:
        errors.append(f"CSV parsing error: {e}")
        return False, errors
    except Exception as e:
        errors.append(f"Unexpected error reading file: {e}")
        return False, errors

    if errors:
        return False, errors

    return True, []


def wait_for_manual_input() -> int:
    """
    Main polling loop.

    Returns:
        int: Exit code (0 for success, 1 for failure/validation error)
    """
    logger = get_logger(__name__)
    logger.info(f"Starting audit sample ingestion wait. Target: {AUDIT_FILE_PATH}")

    retries = 0
    while retries < MAX_RETRIES:
        if AUDIT_FILE_PATH.exists():
            logger.info(f"File detected: {AUDIT_FILE_PATH.name}. Validating schema...")
            is_valid, errors = validate_schema(AUDIT_FILE_PATH)

            if is_valid:
                logger.info("Schema validation PASSED.")
                logger.info("Audit sample ingestion successful.")
                return 0
            else:
                error_msg = "Schema validation FAILED."
                for err in errors:
                    error_msg += f" {err}"
                logger.error(error_msg)
                # If the file exists but is invalid, we should not wait indefinitely.
                # The human must fix the file. We exit with error.
                return 1
        else:
            logger.info(f"File not found. Waiting {POLL_INTERVAL_SECONDS}s...")
            time.sleep(POLL_INTERVAL_SECONDS)
            retries += 1

    logger.error(f"Timeout: File {AUDIT_FILE_PATH} not found after {MAX_RETRIES} attempts.")
    return 1


def main() -> None:
    """Entry point for the script."""
    set_global_seed(42)
    exit_code = wait_for_manual_input()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()