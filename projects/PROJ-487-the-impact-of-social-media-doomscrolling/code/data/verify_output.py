import os
import sys
import logging
import json
from pathlib import Path
from utils.logging import get_logger

def verify_file_exists(file_path: str) -> bool:
    """Check if the specified file exists."""
    path = Path(file_path)
    exists = path.exists()
    if exists:
        logging.info(f"File exists: {file_path}")
    else:
        logging.error(f"File does not exist: {file_path}")
    return exists

def verify_file_non_empty(file_path: str) -> bool:
    """Check if the specified file is non-empty."""
    path = Path(file_path)
    if not path.exists():
        logging.error(f"Cannot check size: file does not exist: {file_path}")
        return False
    
    size = path.stat().st_size
    if size > 0:
        logging.info(f"File is non-empty ({size} bytes): {file_path}")
        return True
    else:
        logging.error(f"File is empty: {file_path}")
        return False

def verify_checksum_exists(checksum_path: str, file_name: str) -> bool:
    """Verify that the checksum for a specific file exists in the checksums JSON."""
    path = Path(checksum_path)
    if not path.exists():
        logging.error(f"Checksum file does not exist: {checksum_path}")
        return False

    try:
        with open(path, 'r') as f:
            checksums = json.load(f)
        
        if file_name in checksums:
            logging.info(f"Checksum found for {file_name} in {checksum_path}")
            return True
        else:
            logging.error(f"Checksum NOT found for {file_name} in {checksum_path}")
            return False
    except json.JSONDecodeError:
        logging.error(f"Invalid JSON in checksum file: {checksum_path}")
        return False
    except Exception as e:
        logging.error(f"Error reading checksum file: {e}")
        return False

def main():
    logger = get_logger()
    logger.info("Starting verification for Google Trends output.")
    
    # Define paths relative to project root
    # Assuming script runs from project root or code/data
    project_root = Path(__file__).resolve().parent.parent.parent
    data_raw_dir = project_root / "data" / "raw"
    csv_file_path = data_raw_dir / "google_trends.csv"
    checksum_file_path = data_raw_dir / ".checksums.json"
    
    all_checks_passed = True

    # 1. Verify file exists
    if not verify_file_exists(str(csv_file_path)):
        all_checks_passed = False
    
    # 2. Verify file is non-empty
    if not verify_file_non_empty(str(csv_file_path)):
        all_checks_passed = False

    # 3. Verify checksum exists for this file
    if not verify_checksum_exists(str(checksum_file_path), "google_trends.csv"):
        all_checks_passed = False

    if all_checks_passed:
        logger.info("All verification checks passed for google_trends.csv.")
        sys.exit(0)
    else:
        logger.error("Verification failed for google_trends.csv.")
        sys.exit(1)

if __name__ == "__main__":
    main()