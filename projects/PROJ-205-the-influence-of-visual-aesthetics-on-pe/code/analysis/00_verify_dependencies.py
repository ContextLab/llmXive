"""
Dependency Verification Script (T024b).

Verifies that preprocessing has run successfully and checksums match
before allowing analysis scripts to proceed.
"""
import os
import sys
import json
import argparse
from pathlib import Path
import hashlib

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.helpers import get_project_root, get_submissions_csv_path, get_cleaned_csv_path
from utils.checksums import load_checksums, get_checksum_store_path


def verify_dependencies() -> bool:
    """
    Verify that all required dependencies are present.
    
    Returns:
        True if all dependencies are satisfied.
        
    Raises:
        FileNotFoundError: If required files are missing.
        RuntimeError: If checksums do not match.
    """
    root = get_project_root()
    
    # 1. Check for raw submissions file
    raw_csv = get_submissions_csv_path()
    if not raw_csv.exists():
        raise FileNotFoundError(
            f"Raw submissions file not found: {raw_csv}. "
            "Please run the survey or generate mock data first."
        )
    
    # 2. Check for checksum file
    checksum_file = get_checksum_store_path()
    if not checksum_file.exists():
        raise FileNotFoundError(
            f"Checksum file not found: {checksum_file}. "
            "Run preprocessing or data generation to create checksums."
        )
    
    # 3. Verify raw data checksum
    checksums = load_checksums(checksum_file)
    if "submissions.csv" not in checksums:
        raise RuntimeError("Checksum for submissions.csv not found in checksum file.")
        
    expected_hash = checksums["submissions.csv"]
    
    # Compute actual hash
    sha256_hash = hashlib.sha256()
    with open(raw_csv, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    actual_hash = sha256_hash.hexdigest()
    
    if actual_hash != expected_hash:
        raise RuntimeError(
            f"Checksum mismatch for submissions.csv. "
            f"Expected: {expected_hash}, Actual: {actual_hash}. "
            "Data may have been modified since last checksum."
        )
    
    # 4. Check for cleaned data file (output of 00_preprocess.py)
    cleaned_csv = get_cleaned_csv_path()
    if not cleaned_csv.exists():
        raise FileNotFoundError(
            f"Cleaned data file not found: {cleaned_csv}. "
            "Run code/analysis/00_preprocess.py first."
        )
    
    return True


def main():
    """Main entry point."""
    print("Verifying analysis dependencies...")
    try:
        verify_dependencies()
        print("All dependencies verified successfully.")
        return 0
    except (FileNotFoundError, RuntimeError) as e:
        print(f"Dependency verification FAILED: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())