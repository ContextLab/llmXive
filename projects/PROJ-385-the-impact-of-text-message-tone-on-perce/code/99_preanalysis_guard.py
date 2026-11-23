"""
Pre‑analysis guard for the LMM script.

This guard ensures that ``data/processed/anonymised_ratings.csv`` exists,
validates against ``specs/001-the-impact-of-text-message-tone-on-perce/contracts/rating.schema.yaml``,
and contains no PII (specifically checking for raw Prolific ID patterns).
It is intended to be run as part of the pipeline; the script exits with
status 0 when the guard passes and with status 1 (and an explanatory message)
when it fails.
"""

import sys
import os
import re
import csv
from pathlib import Path

# Import project utilities
from config import get_processed_data_dir, get_contracts_dir
from logging_config import setup_logging, get_logger

# Setup logging
logger = setup_logging()
logger = get_logger(__name__)

# Paths
PROCESSED_DATA_DIR = get_processed_data_dir()
CONTRACTS_DIR = get_contracts_dir()
ANONYMISED_RATINGS_FILE = PROCESSED_DATA_DIR / "anonymised_ratings.csv"
RATING_SCHEMA_FILE = CONTRACTS_DIR / "rating.schema.yaml"

# Regex patterns for PII detection (Prolific ID format: typically alphanumeric, e.g., "a1b2c3d4e5f6g7h8")
# Prolific IDs are usually 24 characters long alphanumeric strings.
# We check for patterns that look like raw IDs in the participant_id or prolific_id columns.
PROLIFIC_ID_PATTERN = re.compile(r'^[a-zA-Z0-9]{12,32}$')


def _check_file_exists() -> bool:
    """Check if the anonymised ratings file exists."""
    if not ANONYMISED_RATINGS_FILE.exists():
        logger.error(f"Guard failure: File not found: {ANONYMISED_RATINGS_FILE}")
        return False
    logger.info(f"File found: {ANONYMISED_RATINGS_FILE}")
    return True


def _validate_schema() -> bool:
    """
    Validate the CSV against the rating.schema.yaml.
    We perform a basic structural validation: check required columns exist.
    For a full schema validation, we would use a library like jsonschema or cerberus,
    but here we assume the schema defines required columns.
    """
    if not RATING_SCHEMA_FILE.exists():
        logger.error(f"Guard failure: Schema file not found: {RATING_SCHEMA_FILE}")
        return False

    # Load schema to extract required columns
    try:
        import yaml
        with open(RATING_SCHEMA_FILE, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Guard failure: Could not load schema: {e}")
        return False

    # Expected required columns based on typical rating schema (adjust if schema differs)
    # The schema usually defines 'properties'. We look for required fields.
    required_columns = schema.get('required', [])
    properties = schema.get('properties', {})

    if not required_columns:
        # If no required fields in schema, try to infer from properties keys
        required_columns = list(properties.keys())

    if not required_columns:
        logger.warning("Guard warning: No required columns found in schema. Skipping column check.")
        return True

    try:
        with open(ANONYMISED_RATINGS_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            if not fieldnames:
                logger.error("Guard failure: CSV file is empty or has no headers.")
                return False

            missing_cols = set(required_columns) - set(fieldnames)
            if missing_cols:
                logger.error(f"Guard failure: Missing required columns: {missing_cols}")
                return False

            # Read first row to check for empty data if needed, but schema usually covers structure
            # We assume if headers are present and match, the file is structurally valid enough for this guard.
            logger.info(f"Schema validation passed. Required columns present: {required_columns}")
            return True

    except Exception as e:
        logger.error(f"Guard failure: Error reading CSV for schema validation: {e}")
        return False


def _check_pii() -> bool:
    """
    Check for PII in the anonymised ratings file.
    Specifically, we look for raw Prolific IDs in the 'participant_id' or 'prolific_id' columns.
    If the data is properly anonymised, these columns should contain hashed values or non-matching patterns.
    """
    try:
        with open(ANONYMISED_RATINGS_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames

            # Identify potential PII columns
            pii_candidates = [col for col in fieldnames if 'prolific' in col.lower() or 'participant' in col.lower()]
            if not pii_candidates:
                logger.warning("Guard warning: No obvious PII columns found to check.")
                return True

            for row in reader:
                for col in pii_candidates:
                    value = row.get(col, '')
                    if value and PROLIFIC_ID_PATTERN.match(value):
                        # If a value matches the typical Prolific ID pattern, it might be raw PII.
                        # However, hashed values might also match if not careful.
                        # We assume that if a column named 'prolific_id' contains a 24-char alphanumeric string,
                        # it is likely raw PII unless explicitly stated otherwise in the anonymisation process.
                        # To be safe, we check if the value looks like a raw ID.
                        # A more robust check would compare against a list of known hashes, but that's not available here.
                        # We assume that a valid anonymisation would not produce a string matching the raw ID pattern
                        # unless the hash function is weak or the ID is not hashed.
                        # For this guard, we flag if we see a pattern that strongly resembles a raw Prolific ID.
                        logger.error(f"Guard failure: Potential PII detected in column '{col}': {value}")
                        return False

            logger.info("PII check passed: No raw Prolific ID patterns detected.")
            return True

    except Exception as e:
        logger.error(f"Guard failure: Error checking PII: {e}")
        return False


def check_lmm_script() -> None:
    """
    Perform the guard checks.

    * Fail if `data/processed/anonymised_ratings.csv` is absent.
    * Fail if the file does not validate against `rating.schema.yaml`.
    * Fail if the file contains PII.
    """
    logger.info("Starting pre-analysis guard checks...")

    if not _check_file_exists():
        sys.exit(1)

    if not _validate_schema():
        sys.exit(1)

    if not _check_pii():
        sys.exit(1)

    logger.info("Pre‑analysis guard passed: All checks successful.")
    sys.exit(0)


def main():
    """CLI entry point."""
    check_lmm_script()


if __name__ == "__main__":
    main()
