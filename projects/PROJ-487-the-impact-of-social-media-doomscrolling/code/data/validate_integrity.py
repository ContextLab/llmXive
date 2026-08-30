import os
import sys
import json
import logging
import hashlib
from datetime import datetime
from pathlib import Path

# Import from sibling utils if available, otherwise define locally to ensure standalone execution
# The API surface indicates utils.logging exists, but we need standard logging for this script
from utils.logging import get_logger

logger = get_logger(__name__)

def calculate_md5(file_path: str) -> str:
    """Calculate MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error calculating MD5 for {file_path}: {e}")
        raise

def read_checksum_file(checksum_path: str) -> str:
    """Read the expected MD5 checksum from a .md5 file."""
    try:
        with open(checksum_path, "r") as f:
            # The file usually contains "hash  filename" or just "hash"
            content = f.read().strip()
            parts = content.split()
            if len(parts) >= 1:
                return parts[0]
            return content
    except FileNotFoundError:
        logger.error(f"Checksum file not found: {checksum_path}")
        raise
    except Exception as e:
        logger.error(f"Error reading checksum file {checksum_path}: {e}")
        raise

def check_csv_integrity(csv_path: str) -> bool:
    """
    Check if a CSV file has non-empty rows (header + at least one data row).
    Returns True if valid, False otherwise.
    """
    try:
        with open(csv_path, "r") as f:
            lines = f.readlines()
            if len(lines) < 2:
                logger.error(f"File {csv_path} has fewer than 2 lines (header + data).")
                return False
            # Check if the second line (first data row) is not just whitespace
            if not lines[1].strip():
                logger.error(f"File {csv_path} has an empty first data row.")
                return False
            logger.info(f"File {csv_path} has non-empty rows.")
            return True
    except FileNotFoundError:
        logger.error(f"File not found: {csv_path}")
        return False
    except Exception as e:
        logger.error(f"Error checking integrity of {csv_path}: {e}")
        return False

def main():
    """
    Main entry point for T015: Data Integrity Verification.
    Verifies:
    1. data/raw/gdelt_events.csv exists, has non-empty rows, and MD5 matches.
    2. data/raw/google_trends.csv exists, has non-empty rows, and MD5 matches.
    Exits with non-zero status on failure.
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    data_raw_dir = project_root / "data" / "raw"

    files_to_check = [
        ("gdelt_events.csv", data_raw_dir / "gdelt_events.csv"),
        ("google_trends.csv", data_raw_dir / "google_trends.csv")
    ]

    all_valid = True

    for name, csv_path in files_to_check:
        checksum_path = csv_path.with_suffix(".md5")
        
        logger.info(f"--- Validating {name} ---")

        # 1. Check file existence
        if not csv_path.exists():
            logger.error(f"CRITICAL: {name} does not exist at {csv_path}.")
            all_valid = False
            continue

        # 2. Check non-empty rows
        if not check_csv_integrity(str(csv_path)):
            logger.error(f"CRITICAL: {name} does not have non-empty rows.")
            all_valid = False
            continue

        # 3. Verify MD5 checksum
        if not checksum_path.exists():
            logger.error(f"CRITICAL: Checksum file {checksum_path} not found.")
            all_valid = False
            continue

        try:
            calculated_md5 = calculate_md5(str(csv_path))
            expected_md5 = read_checksum_file(str(checksum_path))

            if calculated_md5 == expected_md5:
                logger.info(f"SUCCESS: {name} MD5 checksum matches ({calculated_md5}).")
            else:
                logger.error(f"CRITICAL: {name} MD5 mismatch.")
                logger.error(f"  Expected: {expected_md5}")
                logger.error(f"  Calculated: {calculated_md5}")
                all_valid = False
        except Exception as e:
            logger.error(f"CRITICAL: Error verifying checksum for {name}: {e}")
            all_valid = False

    if all_valid:
        logger.info("=" * 50)
        logger.info("DATA INTEGRITY CHECK PASSED.")
        logger.info("=" * 50)
        sys.exit(0)
    else:
        logger.info("=" * 50)
        logger.error("DATA INTEGRITY CHECK FAILED.")
        logger.info("=" * 50)
        sys.exit(1)

if __name__ == "__main__":
    main()