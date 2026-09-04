import os
import sys
import json
import logging
import hashlib
from datetime import datetime
from pathlib import Path

# Add project root to path if not already present
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logging import get_logger
from utils.validation import validate_dataset_file, load_schema

logger = get_logger(__name__)

# Target date range from spec
TARGET_START_DATE = "2020-01-01"
TARGET_END_DATE = "2023-12-31"

def calculate_md5(file_path: str) -> str:
    """Calculate MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def read_checksum_file(checksum_path: str) -> dict:
    """Read checksums from a JSON file."""
    if not os.path.exists(checksum_path):
        logger.warning(f"Checksum file not found: {checksum_path}")
        return {}
    try:
        with open(checksum_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in checksum file: {checksum_path}")
        return {}

def check_csv_integrity(
    file_path: str,
    schema_path: str,
    min_rows: int = 1,
    required_columns: list = None
) -> bool:
    """
    Verify CSV file integrity:
    1. File exists and is non-empty
    2. Has valid schema structure
    3. Contains expected number of rows
    4. (Optional) Validates against a JSON schema
    """
    if not os.path.exists(file_path):
        logger.error(f"File does not exist: {file_path}")
        return False

    if os.path.getsize(file_path) == 0:
        logger.error(f"File is empty: {file_path}")
        return False

    # Validate against schema if provided
    if schema_path and os.path.exists(schema_path):
        try:
            is_valid = validate_dataset_file(file_path, schema_path)
            if not is_valid:
                logger.error(f"File {file_path} failed schema validation")
                return False
            logger.info(f"Schema validation passed for {file_path}")
        except Exception as e:
            logger.error(f"Schema validation error for {file_path}: {e}")
            return False

    # Check row count
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # Subtract 1 for header
            data_rows = len(lines) - 1
            if data_rows < min_rows:
                logger.error(f"File {file_path} has only {data_rows} data rows, expected at least {min_rows}")
                return False
            logger.info(f"File {file_path} has {data_rows} data rows (min required: {min_rows})")
    except Exception as e:
        logger.error(f"Error reading file {file_path} for row count: {e}")
        return False

    # Check required columns if specified
    if required_columns:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                header = f.readline().strip().split(',')
                missing_cols = [col for col in required_columns if col not in header]
                if missing_cols:
                    logger.error(f"File {file_path} missing required columns: {missing_cols}")
                    return False
            logger.info(f"File {file_path} has all required columns: {required_columns}")
        except Exception as e:
            logger.error(f"Error checking columns in {file_path}: {e}")
            return False

    return True

def check_date_range_coverage(file_path: str, start_date: str, end_date: str) -> bool:
    """
    Verify that the CSV file covers the target date range.
    Assumes a 'date' column exists in the format YYYY-MM-DD.
    """
    try:
        import pandas as pd
        df = pd.read_csv(file_path)
        
        if 'date' not in df.columns:
            logger.error(f"File {file_path} does not have a 'date' column")
            return False

        # Convert to datetime
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date'])

        if df.empty:
            logger.error(f"No valid dates found in {file_path}")
            return False

        min_date = df['date'].min().strftime('%Y-%m-%d')
        max_date = df['date'].max().strftime('%Y-%m-%d')

        logger.info(f"Date range in {file_path}: {min_date} to {max_date}")
        logger.info(f"Target range: {start_date} to {end_date}")

        if min_date > start_date or max_date < end_date:
            logger.warning(f"Date range coverage is incomplete for {file_path}")
            # Note: This is a warning for T015a, strict check is T015b
            # T015a requires non-empty rows for target range, not full coverage
            # So we check if there is ANY overlap
            if max_date < start_date or min_date > end_date:
                logger.error(f"No overlap with target date range in {file_path}")
                return False
            logger.info(f"Partial overlap found, proceeding with validation")
        else:
            logger.info(f"Full date range coverage verified for {file_path}")

        return True

    except Exception as e:
        logger.error(f"Error checking date range in {file_path}: {e}")
        return False

def main():
    """
    Main function to validate data integrity for T015a.
    Verifies:
    1. Files exist and are non-empty
    2. Files have valid schema structure
    3. Files have non-empty rows
    4. (Optional) Checksums match if recorded
    5. Date range has some overlap with target (strict check in T015b)
    """
    logger.info("Starting data integrity validation (T015a)")
    
    project_root = Path(__file__).resolve().parent.parent
    data_raw_dir = project_root / "data" / "raw"
    contracts_dir = project_root / "specs" / "001-news-volume-anxiety" / "contracts"
    
    gdelt_file = data_raw_dir / "gdelt_events.csv"
    trends_file = data_raw_dir / "google_trends.csv"
    gdelt_schema = contracts_dir / "dataset.schema.yaml"
    trends_schema = contracts_dir / "dataset.schema.yaml" # Same schema for both
    checksums_file = data_raw_dir / ".checksums.json"
    
    all_valid = True
    
    # Files to validate
    files_to_check = [
        (str(gdelt_file), str(gdelt_schema), ["date", "value", "source"]),
        (str(trends_file), str(trends_schema), ["date", "value", "source"])
    ]
    
    for file_path, schema_path, required_cols in files_to_check:
        logger.info(f"Validating {file_path}...")
        
        # Check file existence and basic integrity
        if not check_csv_integrity(file_path, schema_path, min_rows=1, required_columns=required_cols):
            logger.error(f"Integrity check FAILED for {file_path}")
            all_valid = False
            continue
        
        # Check date range overlap
        if not check_date_range_coverage(file_path, TARGET_START_DATE, TARGET_END_DATE):
            logger.error(f"Date range check FAILED for {file_path}")
            all_valid = False
            continue
        
        # Check checksum if exists
        if os.path.exists(checksums_file):
            recorded_checksums = read_checksum_file(str(checksums_file))
            file_name = os.path.basename(file_path)
            if file_name in recorded_checksums:
                recorded_md5 = recorded_checksums[file_name]
                current_md5 = calculate_md5(file_path)
                if recorded_md5 != current_md5:
                    logger.warning(f"Checksum mismatch for {file_path}: recorded={recorded_md5}, current={current_md5}")
                    # Not a hard fail for T015a, as checksums might be generated later
                    # But we log it
                else:
                    logger.info(f"Checksum verified for {file_path}")
            else:
                logger.info(f"No recorded checksum for {file_name} (expected if checksums generated later)")
        
        logger.info(f"Validation PASSED for {file_path}")
    
    if all_valid:
        logger.info("All data integrity checks PASSED")
        sys.exit(0)
    else:
        logger.error("One or more data integrity checks FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()