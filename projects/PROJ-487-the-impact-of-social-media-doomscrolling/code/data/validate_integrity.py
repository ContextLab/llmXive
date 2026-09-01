import os
import sys
import json
import logging
import hashlib
from datetime import datetime
from pathlib import Path
from utils.logging import get_logger

logger = get_logger(__name__)

def calculate_md5(filepath: str) -> str:
    """Calculate MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def read_checksum_file(checksum_path: str) -> dict:
    """Read the checksums JSON file."""
    with open(checksum_path, 'r') as f:
        return json.load(f)

def check_csv_integrity(csv_path: str, expected_checksum: str) -> bool:
    """Check if a CSV file's MD5 matches the expected checksum."""
    if not os.path.exists(csv_path):
        logger.error(f"File not found: {csv_path}")
        return False

    if os.path.getsize(csv_path) == 0:
        logger.error(f"File is empty: {csv_path}")
        return False

    actual_checksum = calculate_md5(csv_path)
    if actual_checksum != expected_checksum:
        logger.error(f"Checksum mismatch for {csv_path}. Expected: {expected_checksum}, Got: {actual_checksum}")
        return False

    # Check for non-empty rows (excluding header)
    with open(csv_path, 'r') as f:
        lines = f.readlines()
        if len(lines) <= 1:
            logger.error(f"No data rows in {csv_path}")
            return False

    logger.info(f"Integrity check passed for {csv_path}")
    return True

def main():
    """Main entry point for data integrity verification."""
    logger.info("Starting data integrity verification...")

    project_root = Path(__file__).resolve().parents[2]
    data_raw_dir = project_root / "data" / "raw"
    checksum_file = data_raw_dir / ".checksums.json"

    if not checksum_file.exists():
        logger.error(f"Checksum file not found: {checksum_file}")
        sys.exit(1)

    try:
        checksums = read_checksum_file(str(checksum_file))
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse checksum file: {e}")
        sys.exit(1)

    files_to_check = [
        "gdelt_events.csv",
        "google_trends.csv"
    ]

    all_passed = True

    for filename in files_to_check:
        filepath = data_raw_dir / filename
        expected_checksum = checksums.get(filename)

        if not expected_checksum:
            logger.warning(f"No checksum found for {filename} in {checksum_file}")
            all_passed = False
            continue

        logger.info(f"Verifying {filename}...")
        if not check_csv_integrity(str(filepath), expected_checksum):
            all_passed = False

    if all_passed:
        logger.info("All integrity checks passed.")
        sys.exit(0)
    else:
        logger.error("One or more integrity checks failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()