"""
T086: Validate Participant entity.

Ensures that `data/processed/anonymised_ratings.csv` contains a non-null
`participant_id` column matching the Participant schema requirements.

Verification:
  - File exists at `data/processed/anonymised_ratings.csv`.
  - Column `participant_id` exists.
  - All values in `participant_id` are non-null (no empty strings or NaN).
  - Values match the expected format (alphanumeric hash, typically 32-64 chars).
"""
import csv
import re
import sys
import logging
from pathlib import Path
from config import get_processed_data_dir
from logging_config import setup_logging, get_logger

# Expected schema pattern for a hashed participant ID (alphanumeric, length 32-64)
# This matches the output of `hash_prolific_id` in 05_anonymise_ratings.py
PARTICIPANT_ID_PATTERN = re.compile(r'^[a-f0-9]{32,64}$')

def validate_participant_entity() -> bool:
    """
    Validates the Participant entity in the anonymised ratings file.
    
    Returns:
        bool: True if validation passes, False otherwise.
    """
    setup_logging()
    logger = get_logger(__name__)
    
    processed_dir = get_processed_data_dir()
    input_path = processed_dir / "anonymised_ratings.csv"
    
    if not input_path.exists():
        logger.error(f"Validation failed: File not found at {input_path}")
        return False
    
    logger.info(f"Validating participant entity in {input_path}")
    
    try:
        with open(input_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Check 1: Column exists
            if reader.fieldnames is None:
                logger.error("Validation failed: CSV file is empty or has no headers.")
                return False
            
            if 'participant_id' not in reader.fieldnames:
                logger.error(
                    f"Validation failed: Missing required column 'participant_id'. "
                    f"Found columns: {reader.fieldnames}"
                )
                return False
            
            invalid_count = 0
            total_count = 0
            null_count = 0
            
            for row_num, row in enumerate(reader, start=2): # Start at 2 (header is 1)
                total_count += 1
                pid = row.get('participant_id')
                
                # Check 2: Non-null
                if pid is None or pid.strip() == '':
                    null_count += 1
                    invalid_count += 1
                    logger.warning(f"Row {row_num}: 'participant_id' is null or empty.")
                    continue
                
                pid = pid.strip()
                
                # Check 3: Format validation (Hashed ID)
                if not PARTICIPANT_ID_PATTERN.match(pid):
                    invalid_count += 1
                    logger.warning(
                        f"Row {row_num}: 'participant_id' '{pid}' does not match "
                        f"expected hash format (alphanumeric, 32-64 chars)."
                    )
            
            if null_count > 0:
                logger.error(
                    f"Validation failed: Found {null_count} rows with null/empty 'participant_id'."
                )
                return False
            
            if invalid_count > 0:
                logger.error(
                    f"Validation failed: Found {invalid_count} rows with malformed 'participant_id'."
                )
                return False
            
            logger.info(
                f"Validation passed: {total_count} records checked. "
                f"All 'participant_id' values are non-null and valid."
            )
            return True

    except Exception as e:
        logger.error(f"Validation failed with unexpected error: {e}", exc_info=True)
        return False

def main():
    """CLI entry point for T086."""
    success = validate_participant_entity()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
