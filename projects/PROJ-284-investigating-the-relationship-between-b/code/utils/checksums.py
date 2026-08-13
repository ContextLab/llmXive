"""Checksum verification utility for the pipeline.

This script verifies the integrity of processed data files using SHA-256 checksums.
It reads checksums from `data/processed/checksums.json` and validates the corresponding
files in `data/processed/`.

Usage:
    python code/utils/checksums.py verify
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from code.logging_config import get_logger

logger = get_logger(__name__)

CHECKSUMS_FILE = Path("data/processed/checksums.json")
PROCESSED_DIR = Path("data/processed")


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def load_checksums() -> Dict[str, str]:
    """Load expected checksums from JSON file."""
    if not CHECKSUMS_FILE.exists():
        raise FileNotFoundError(f"Checksums file not found: {CHECKSUMS_FILE}")
    
    with open(CHECKSUMS_FILE, "r") as f:
        return json.load(f)


def verify_checksums() -> Tuple[bool, List[str], List[str]]:
    """Verify all files against their stored checksums.
    
    Returns:
        Tuple of (all_passed, list_of_valid_files, list_of_failed_files)
    """
    if not CHECKSUMS_FILE.exists():
        logger.log("checksums_missing", path=str(CHECKSUMS_FILE))
        return False, [], [f"Checksums file missing: {CHECKSUMS_FILE}"]
    
    expected_checksums = load_checksums()
    all_passed = True
    valid_files = []
    failed_files = []
    
    if not expected_checksums:
        logger.log("checksums_empty")
        return True, [], []
    
    for relative_path, expected_hash in expected_checksums.items():
        file_path = PROCESSED_DIR / relative_path
        
        if not file_path.exists():
            all_passed = False
            msg = f"File missing: {file_path}"
            failed_files.append(msg)
            logger.log("file_missing", path=str(file_path))
            continue
        
        try:
            actual_hash = compute_sha256(file_path)
            if actual_hash == expected_hash:
                valid_files.append(str(file_path))
                logger.log("checksum_verified", path=str(file_path), hash=actual_hash)
            else:
                all_passed = False
                msg = f"Checksum mismatch: {file_path} (expected: {expected_hash}, got: {actual_hash})"
                failed_files.append(msg)
                logger.log("checksum_mismatch", 
                         path=str(file_path), 
                         expected=expected_hash, 
                         actual=actual_hash)
        except Exception as e:
            all_passed = False
            msg = f"Error reading {file_path}: {str(e)}"
            failed_files.append(msg)
            logger.log("read_error", path=str(file_path), error=str(e))
    
    return all_passed, valid_files, failed_files


def main() -> int:
    """Main entry point for checksum verification."""
    parser = argparse.ArgumentParser(
        description="Verify checksums of processed data files"
    )
    parser.add_argument(
        "command",
        choices=["verify"],
        help="Command to execute"
    )
    
    args = parser.parse_args()
    
    if args.command == "verify":
        logger.log("checksum_verification_start")
        
        if not PROCESSED_DIR.exists():
            logger.log("processed_dir_missing", path=str(PROCESSED_DIR))
            print("Error: data/processed directory does not exist.")
            return 1
        
        all_passed, valid_files, failed_files = verify_checksums()
        
        print(f"\nChecksum Verification Results:")
        print(f"{'='*50}")
        print(f"Total files checked: {len(valid_files) + len(failed_files)}")
        print(f"Valid files: {len(valid_files)}")
        print(f"Failed files: {len(failed_files)}")
        
        if valid_files:
            print(f"\nValid files:")
            for f in valid_files:
                print(f"  ✓ {f}")
        
        if failed_files:
            print(f"\nFailed files:")
            for f in failed_files:
                print(f"  ✗ {f}")
        
        print(f"{'='*50}")
        
        if all_passed:
            print("All checksums verified successfully.")
            logger.log("checksum_verification_success")
            return 0
        else:
            print("Checksum verification FAILED.")
            logger.log("checksum_verification_failed", 
                     failed_count=len(failed_files))
            return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())