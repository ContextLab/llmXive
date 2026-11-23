"""
Unify ASSISTments and Khan Academy datasets into a single schema.

This script merges data/raw/assistments.csv and data/raw/khan_academy.csv
into a single unified schema data/raw/unified_problems.csv.

Requirements:
- Both source files must exist.
- Both source files must contain required fields: problem_id, prompt_text, difficulty, skill.
- Output: data/raw/unified_problems.csv with checksum.
"""

import os
import sys
import csv
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Set

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
RAW_DATA_DIR = Path("data/raw")
ASSISTMENTS_FILE = RAW_DATA_DIR / "assistments.csv"
KHAN_ACADEMY_FILE = RAW_DATA_DIR / "khan_academy.csv"
UNIFIED_FILE = RAW_DATA_DIR / "unified_problems.csv"
CHECKSUM_FILE = RAW_DATA_DIR / "unified_problems.csv.sha256"

REQUIRED_FIELDS: Set[str] = {"problem_id", "prompt_text", "difficulty", "skill"}


def validate_file_exists(file_path: Path) -> bool:
    """Check if the file exists."""
    if not file_path.exists():
        logger.error(f"Source file not found: {file_path}")
        return False
    return True


def validate_columns(file_path: Path, required: Set[str]) -> bool:
    """
    Validate that the CSV file contains all required columns.
    Returns True if valid, False otherwise.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                logger.error(f"File {file_path} appears to be empty or has no header.")
                return False

            actual_fields = set(reader.fieldnames)
            missing = required - actual_fields

            if missing:
                logger.error(
                    f"File {file_path} is missing required columns: {missing}. "
                    f"Found: {actual_fields}"
                )
                return False

        logger.info(f"Validation passed for {file_path.name}: all required columns present.")
        return True

    except Exception as e:
        logger.error(f"Error validating columns in {file_path}: {e}")
        return False


def load_csv_to_dicts(file_path: Path) -> List[Dict[str, Any]]:
    """Load a CSV file into a list of dictionaries."""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data


def unify_datasets() -> bool:
    """
    Main logic to unify the datasets.
    Returns True if successful, False otherwise.
    """
    logger.info("Starting dataset unification process...")

    # 1. Validate existence
    if not validate_file_exists(ASSISTMENTS_FILE):
        return False
    if not validate_file_exists(KHAN_ACADEMY_FILE):
        return False

    # 2. Validate schema
    if not validate_columns(ASSISTMENTS_FILE, REQUIRED_FIELDS):
        return False
    if not validate_columns(KHAN_ACADEMY_FILE, REQUIRED_FIELDS):
        return False

    # 3. Load data
    logger.info(f"Loading {ASSISTMENTS_FILE.name}...")
    assistments_data = load_csv_to_dicts(ASSISTMENTS_FILE)
    logger.info(f"Loaded {len(assistments_data)} records from ASSISTments.")

    logger.info(f"Loading {KHAN_ACADEMY_FILE.name}...")
    khan_data = load_csv_to_dicts(KHAN_ACADEMY_FILE)
    logger.info(f"Loaded {len(khan_data)} records from Khan Academy.")

    # 4. Merge data
    unified_data = assistments_data + khan_data
    logger.info(f"Total merged records: {len(unified_data)}")

    # 5. Write unified CSV
    logger.info(f"Writing unified data to {UNIFIED_FILE}...")
    try:
        with open(UNIFIED_FILE, 'w', newline='', encoding='utf-8') as f:
            # Ensure consistent field order
            fieldnames = ["problem_id", "prompt_text", "difficulty", "skill"]
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(unified_data)
        logger.info(f"Successfully wrote {len(unified_data)} records to {UNIFIED_FILE}")
    except Exception as e:
        logger.error(f"Failed to write unified CSV: {e}")
        return False

    # 6. Generate checksum
    logger.info("Generating SHA256 checksum...")
    sha256_hash = hashlib.sha256()
    try:
        with open(UNIFIED_FILE, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        checksum = sha256_hash.hexdigest()

        with open(CHECKSUM_FILE, "w", encoding="utf-8") as f:
            f.write(f"{checksum}  {UNIFIED_FILE.name}\n")

        logger.info(f"Checksum generated: {checksum}")
        logger.info(f"Checksum saved to {CHECKSUM_FILE}")

    except Exception as e:
        logger.error(f"Failed to generate checksum: {e}")
        return False

    logger.info("Dataset unification completed successfully.")
    return True


def main():
    """Entry point."""
    success = unify_datasets()
    if not success:
        logger.error("Dataset unification failed. Aborting.")
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
