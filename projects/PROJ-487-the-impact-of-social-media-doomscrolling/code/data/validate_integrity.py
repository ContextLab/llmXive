import os
import sys
import json
import logging
import hashlib
from datetime import datetime
from pathlib import Path
import yaml

# Add project root to path to allow imports if run as script
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logging import get_logger

logger = get_logger(__name__)

def calculate_md5(file_path: str) -> str:
    """Calculate MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def read_checksum_file(state_path: str) -> dict:
    """Read the state YAML file and extract artifact_hashes."""
    if not os.path.exists(state_path):
        raise FileNotFoundError(f"State file not found: {state_path}")
    
    with open(state_path, 'r') as f:
        state = yaml.safe_load(f)
    
    if 'artifact_hashes' not in state:
        raise KeyError("State file does not contain 'artifact_hashes' key")
    
    return state['artifact_hashes']

def check_csv_integrity(file_path: str, expected_md5: str) -> bool:
    """Check if a CSV file is non-empty and matches the expected MD5."""
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return False
    
    if os.path.getsize(file_path) == 0:
        logger.error(f"File is empty: {file_path}")
        return False
    
    # Read first few lines to ensure it's not just headers
    with open(file_path, 'r') as f:
        lines = f.readlines()
        if len(lines) < 2:
            logger.error(f"File has no data rows (only header or empty): {file_path}")
            return False
    
    actual_md5 = calculate_md5(file_path)
    if actual_md5 != expected_md5:
        logger.error(f"MD5 mismatch for {file_path}: expected {expected_md5}, got {actual_md5}")
        return False
    
    logger.info(f"Integrity check passed for {file_path} (MD5: {actual_md5})")
    return True

def check_date_range_coverage(file_path: str, start_date: str, end_date: str) -> bool:
    """Verify that the CSV covers the target date range."""
    import pandas as pd
    
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        logger.error(f"Failed to read {file_path}: {e}")
        return False
    
    if 'date' not in df.columns:
        logger.error(f"'date' column not found in {file_path}")
        return False
    
    # Parse dates
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    if df['date'].isnull().all():
        logger.error(f"Failed to parse dates in {file_path}")
        return False
    
    min_date = df['date'].min().strftime('%Y-%m-%d')
    max_date = df['date'].max().strftime('%Y-%m-%d')
    
    logger.info(f"Date range in {file_path}: {min_date} to {max_date}")
    
    if min_date > start_date or max_date < end_date:
        logger.error(f"Date range in {file_path} does not cover {start_date} to {end_date}")
        return False
    
    return True

def main():
    """
    T015a: Data Integrity Verification.
    Verifies:
    1. Files exist and are non-empty.
    2. MD5 checksums match recorded values in state file.
    3. (Implicitly via T015b/c flow) Date range coverage.
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    state_file = project_root / "state" / "projects" / "PROJ-487-the-impact-of-social-media-doomscrolling.yaml"
    
    gdelt_file = project_root / "data" / "raw" / "gdelt_events.csv"
    trends_file = project_root / "data" / "raw" / "google_trends.csv"
    
    target_start = "2020-01-01"
    target_end = "2023-12-31"
    
    all_passed = True
    
    logger.info("Starting Data Integrity Verification (T015a)...")
    
    if not os.path.exists(state_file):
        logger.error(f"State file not found: {state_file}")
        logger.error("Prerequisite T037 (Update State File) may not have completed.")
        sys.exit(1)
    
    try:
        hashes = read_checksum_file(str(state_file))
    except Exception as e:
        logger.error(f"Failed to read state file: {e}")
        sys.exit(1)
    
    files_to_check = [
        ("gdelt_events.csv", gdelt_file, hashes.get("gdelt_events.csv")),
        ("google_trends.csv", trends_file, hashes.get("google_trends.csv"))
    ]
    
    for name, path, expected_hash in files_to_check:
        if expected_hash is None:
            logger.error(f"Checksum for {name} not found in state file.")
            all_passed = False
            continue
        
        if not check_csv_integrity(str(path), expected_hash):
            all_passed = False
            continue
        
        if not check_date_range_coverage(str(path), target_start, target_end):
            all_passed = False
    
    if all_passed:
        logger.info("Data Integrity Verification PASSED.")
        print("SUCCESS: All data integrity checks passed.")
        sys.exit(0)
    else:
        logger.error("Data Integrity Verification FAILED.")
        print("FAILURE: Data integrity checks failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
