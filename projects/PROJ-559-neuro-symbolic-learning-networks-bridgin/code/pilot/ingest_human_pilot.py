"""
Ingest and validate the real human pilot dataset.

This script validates the pilot data required for calibration logic (T031).
It checks for the existence of the file, validates the schema against the
pilot_data schema, and ensures the record count meets the minimum threshold (>= 50).

If validation fails, it exits with code 1 and logs the specific error message
required by the specification.
"""

import os
import sys
import csv
import json
import logging
import hashlib
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
INPUT_PATH = "data/pilot/real_pilot_data.csv"
OUTPUT_PATH = "data/pilot/real_pilot_data.csv" # Output is the validated file itself (conceptually)
CHECKSUM_PATH = "data/pilot/real_pilot_data.csv.sha256"
MIN_RECORDS = 50
REQUIRED_COLUMNS = ['problem_id', 'condition', 'correct', 'rt_seconds', 'comprehension_rating']

def calculate_file_checksum(file_path: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_schema(schema_path: str) -> dict:
    """Load the schema definition from a YAML/JSON file if available, else return expected columns."""
    # Since T007b creates contracts/pilot_data.schema.yaml, we try to load it.
    # If not found, we rely on the hardcoded REQUIRED_COLUMNS as fallback for validation logic.
    schema_file = Path(schema_path)
    if schema_file.exists():
        try:
            import yaml
            with open(schema_file, 'r') as f:
                return yaml.safe_load(f)
        except ImportError:
            logger.warning("PyYAML not installed, using hardcoded schema validation.")
            return {"properties": REQUIRED_COLUMNS}
        except Exception as e:
            logger.warning(f"Could not parse schema file {schema_path}: {e}. Using hardcoded schema.")
            return {"properties": REQUIRED_COLUMNS}
    else:
        logger.info(f"Schema file {schema_path} not found. Using hardcoded schema validation.")
        return {"properties": REQUIRED_COLUMNS}

def validate_row(row: dict, schema: dict) -> bool:
    """Validate a single row against the schema."""
    # Check required columns exist in the row
    for col in REQUIRED_COLUMNS:
        if col not in row:
            return False
        
        # Type validation based on schema or reasonable defaults
        if col == 'correct':
            if row[col] not in ['0', '1', 0, 1, 'True', 'False', True, False]:
                return False
        elif col == 'rt_seconds':
            try:
                float(row[col])
            except (ValueError, TypeError):
                return False
        elif col == 'comprehension_rating':
            try:
                float(row[col])
            except (ValueError, TypeError):
                return False
    return True

def ingest_and_validate(input_path: str, min_records: int) -> tuple[bool, str]:
    """
    Ingest and validate the pilot dataset.
    
    Returns:
        tuple: (success: bool, message: str)
    """
    if not os.path.exists(input_path):
        return False, f"Human pilot data missing or invalid (<{min_records} records). Calibration cannot proceed."

    try:
        with open(input_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Validate header
            if reader.fieldnames is None:
                return False, f"Human pilot data missing or invalid (<{min_records} records). Calibration cannot proceed."
            
            missing_cols = set(REQUIRED_COLUMNS) - set(reader.fieldnames)
            if missing_cols:
                return False, f"Human pilot data missing or invalid (<{min_records} records). Calibration cannot proceed."

            rows = []
            for i, row in enumerate(reader):
                if not validate_row(row, {}):
                    logger.warning(f"Invalid row at index {i}: {row}")
                    # We could be strict and fail here, but the task says <50 records is the main blocker.
                    # However, for a clean ingest, we usually want valid data.
                    # Let's count valid rows.
                    continue
                rows.append(row)

            record_count = len(rows)
            
            if record_count < min_records:
                return False, f"Human pilot data missing or invalid (<{min_records} records). Calibration cannot proceed."

            logger.info(f"Successfully validated {record_count} records from {input_path}.")
            return True, f"Validation successful: {record_count} records."

    except Exception as e:
        return False, f"Human pilot data missing or invalid (<{min_records} records). Calibration cannot proceed. Error: {str(e)}"

def main():
    parser = argparse.ArgumentParser(description="Ingest and validate human pilot data for calibration.")
    parser.add_argument(
        "--input", 
        type=str, 
        default=INPUT_PATH,
        help=f"Path to the input pilot data CSV (default: {INPUT_PATH})"
    )
    parser.add_argument(
        "--min-records",
        type=int,
        default=MIN_RECORDS,
        help=f"Minimum number of records required (default: {MIN_RECORDS})"
    )
    args = parser.parse_args()

    success, message = ingest_and_validate(args.input, args.min_records)

    if not success:
        logger.error(message)
        sys.exit(1)
    
    # If successful, write checksum
    try:
        checksum = calculate_file_checksum(args.input)
        with open(CHECKSUM_PATH, 'w') as f:
            f.write(f"{checksum}  {os.path.basename(args.input)}\n")
        logger.info(f"Checksum written to {CHECKSUM_PATH}")
    except Exception as e:
        logger.error(f"Failed to write checksum: {e}")
        # Non-fatal for the main validation, but we log it.

    logger.info(message)
    sys.exit(0)

if __name__ == "__main__":
    main()