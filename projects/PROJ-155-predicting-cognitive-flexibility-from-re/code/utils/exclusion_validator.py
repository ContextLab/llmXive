"""
Module to validate the exclusion log integrity.

Ensures that data/processed/exclusion_log.csv contains exactly one row 
per excluded subject, preventing duplicate logging or missing entries.
"""
import os
import logging
import pandas as pd
from typing import Tuple, Optional, List, Dict, Any

from code.data.paths import get_processed_path
from code.utils.logging import log_error, log_warning, log_exclusion

# Constants
EXCLUSION_LOG_FILENAME = "exclusion_log.csv"
REQUIRED_COLUMNS = ["Subject_ID", "Exclusion_Reason", "Mean_FD"]
SUBJECT_ID_COL = "Subject_ID"

logger = logging.getLogger(__name__)


def get_exclusion_log_path() -> str:
    """Returns the full path to the exclusion log CSV."""
    return os.path.join(get_processed_path(), EXCLUSION_LOG_FILENAME)


def validate_exclusion_log_uniqueness() -> Tuple[bool, List[str]]:
    """
    Validates that the exclusion log contains exactly one row per Subject_ID.
    
    Returns:
        Tuple[bool, List[str]]: (is_valid, list_of_error_messages)
    """
    log_path = get_exclusion_log_path()
    
    if not os.path.exists(log_path):
        msg = f"Exclusion log not found at {log_path}. Validation cannot proceed."
        logger.warning(msg)
        return False, [msg]
    
    try:
        df = pd.read_csv(log_path)
    except Exception as e:
        msg = f"Failed to read exclusion log: {e}"
        logger.error(msg)
        return False, [msg]
    
    if df.empty:
        # Empty log is valid (no exclusions)
        logger.info("Exclusion log is empty. No duplicates found.")
        return True, []
    
    # Check for required columns
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        msg = f"Exclusion log missing required columns: {missing_cols}"
        logger.error(msg)
        return False, [msg]
    
    # Check for duplicates
    duplicates = df[df.duplicated(subset=[SUBJECT_ID_COL], keep=False)]
    
    if not duplicates.empty:
        duplicate_ids = duplicates[SUBJECT_ID_COL].unique().tolist()
        error_msg = (
            f"Validation failed: Found duplicate Subject_IDs in exclusion log: {duplicate_ids}. "
            f"Expected exactly one row per excluded subject."
        )
        logger.error(error_msg)
        return False, [error_msg]
    
    # Check for non-unique counts explicitly
    subject_counts = df[SUBJECT_ID_COL].value_counts()
    if (subject_counts > 1).any():
        dup_ids = subject_counts[subject_counts > 1].index.tolist()
        error_msg = (
            f"Validation failed: Subject_IDs appear more than once: {dup_ids}."
        )
        logger.error(error_msg)
        return False, [error_msg]
    
    logger.info(
        f"Exclusion log validation passed: {len(df)} unique subjects logged."
    )
    return True, []


def run_exclusion_log_validation_pipeline() -> bool:
    """
    Runs the full validation pipeline for the exclusion log.
    
    Returns:
        bool: True if validation passes, False otherwise.
    """
    logger.info("Starting exclusion log validation pipeline...")
    
    is_valid, errors = validate_exclusion_log_uniqueness()
    
    if not is_valid:
        for err in errors:
            log_error(err)
        logger.error("Exclusion log validation FAILED.")
        return False
    
    logger.info("Exclusion log validation PASSED.")
    return True


def main():
    """Entry point for running the validation as a script."""
    # Initialize logging if not already done
    # (Assuming logging is configured by main.py or earlier tasks)
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    success = run_exclusion_log_validation_pipeline()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())