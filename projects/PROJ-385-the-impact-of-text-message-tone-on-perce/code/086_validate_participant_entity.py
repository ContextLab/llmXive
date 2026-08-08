"""
Implementation of T086: Validate Participant entity.

Script to ensure data/processed/anonymised_ratings.csv contains a non-null
participant_id column matching the Participant schema.

Verification: Script exits with error if column missing or malformed.
"""
import csv
import re
import sys
import logging
from pathlib import Path

from config import get_processed_data_dir
from logging_config import setup_logging, get_logger

# Initialize logging
setup_logging()
logger = get_logger(__name__)

ANONYMISED_RATINGS_PATH = Path(get_processed_data_dir()) / "anonymised_ratings.csv"

# Expected format for a hashed participant ID (SHA-256 is 64 hex characters)
PARTICIPANT_ID_PATTERN = re.compile(r'^[0-9a-f]{64}$')

def validate_participant_entity():
    """
    Validates the Participant entity in the anonymised ratings CSV.
    
    Checks:
    1. File exists.
    2. 'participant_id' column exists.
    3. All values in 'participant_id' are non-null and match the expected hash format.
    
    Returns:
        bool: True if validation passes, False otherwise.
    """
    if not ANONYMISED_RATINGS_PATH.exists():
        logger.error(f"File not found: {ANONYMISED_RATINGS_PATH}")
        logger.error("Ensure T051 (Anonymise ratings) has been run successfully.")
        return False

    logger.info(f"Validating Participant entity in {ANONYMISED_RATINGS_PATH}...")
    
    row_count = 0
    valid_count = 0
    invalid_rows = []

    try:
        with open(ANONYMISED_RATINGS_PATH, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            if reader.fieldnames is None:
                logger.error("CSV file is empty or has no headers.")
                return False

            if 'participant_id' not in reader.fieldnames:
                logger.error(f"Column 'participant_id' missing from headers. Found: {reader.fieldnames}")
                return False

            for row_idx, row in enumerate(reader, start=2):
                row_count += 1
                pid = row.get('participant_id')

                # Check for null/empty
                if pid is None or pid.strip() == '':
                    invalid_rows.append((row_idx, "Empty or null participant_id"))
                    continue

                # Check format
                if not PARTICIPANT_ID_PATTERN.match(pid):
                    invalid_rows.append((row_idx, f"Invalid format: '{pid}'"))
                    continue

                valid_count += 1

        if row_count == 0:
            logger.error("CSV file contains no data rows.")
            return False

        if invalid_rows:
            logger.error(f"Validation failed. Found {len(invalid_rows)} rows with invalid or missing participant_id.")
            for r, e in invalid_rows[:5]:
                logger.error(f"  Row {r}: {e}")
            if len(invalid_rows) > 5:
                logger.error(f"  ... and {len(invalid_rows) - 5} more errors.")
            return False

        logger.info(f"Validation passed. All {valid_count} rows have valid, non-null participant_id.")
        return True

    except Exception as e:
        logger.error(f"An error occurred during validation: {e}", exc_info=True)
        return False

def main():
    """CLI entry point."""
    success = validate_participant_entity()
    if success:
        logger.info("T086 Validation: SUCCESS")
        sys.exit(0)
    else:
        logger.error("T086 Validation: FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()