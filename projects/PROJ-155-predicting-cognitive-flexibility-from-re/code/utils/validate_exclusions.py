"""
Validation script for exclusion logs.

Ensures that data/processed/exclusion_log.csv contains exactly one row
per excluded subject (unique Subject_IDs).

Usage:
    python code/utils/validate_exclusions.py
"""

import os
import sys
import logging
import pandas as pd

# Add project root to path if running as script
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from code.utils.logging import get_exclusion_log_path, init_logging, log_error
from code.data.paths import ensure_dir

logger = logging.getLogger(__name__)

def validate_exclusion_log_uniqueness() -> bool:
    """
    Validates that the exclusion log has exactly one row per unique Subject_ID.

    Returns:
        True if validation passes.

    Raises:
        ValueError: If the row count does not match the number of unique Subject_IDs.
    """
    log_path = get_exclusion_log_path()

    if not os.path.exists(log_path):
        # If the log doesn't exist, it means no exclusions were recorded.
        # This is technically valid (0 rows, 0 unique IDs), but we should log it.
        logger.warning(f"Exclusion log not found at {log_path}. Assuming no exclusions.")
        return True

    try:
        df = pd.read_csv(log_path)
    except Exception as e:
        logger.error(f"Failed to read exclusion log: {e}")
        raise

    if df.empty:
        logger.info("Exclusion log is empty. Validation passed (0 exclusions).")
        return True

    if 'Subject_ID' not in df.columns:
        error_msg = "Exclusion log is missing the 'Subject_ID' column."
        logger.error(error_msg)
        raise ValueError(error_msg)

    total_rows = len(df)
    unique_subjects = df['Subject_ID'].nunique()

    logger.info(f"Exclusion log stats: {total_rows} total rows, {unique_subjects} unique subjects.")

    if total_rows != unique_subjects:
        error_msg = (
            f"Validation failed: Exclusion log has {total_rows} rows but only {unique_subjects} "
            f"unique Subject_IDs. Each excluded subject must have exactly one row."
        )
        log_error(error_msg)
        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.info("Validation passed: One row per unique excluded subject.")
    return True

def run_exclusion_log_validation_pipeline() -> bool:
    """
    Runs the full validation pipeline for the exclusion log.

    Returns:
        True if validation passes.
    """
    logger.info("Starting exclusion log validation pipeline...")
    success = validate_exclusion_log_uniqueness()
    if success:
        logger.info("Exclusion log validation pipeline completed successfully.")
    return success

def main():
    """Entry point for the script."""
    init_logging()
    logger.info("Running exclusion log validation (T016)...")

    try:
        run_exclusion_log_validation_pipeline()
        logger.info("Validation PASSED.")
        sys.exit(0)
    except ValueError as e:
        logger.error(f"Validation FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()