"""
Checksum verification script for raw data integrity.

This script verifies the integrity of raw data files by comparing their
computed SHA-256 checksums against expected values stored in a manifest file.

Usage:
    python code/verify_checksums.py

The script expects:
    1. A manifest file at data/raw/manifest.json containing filename -> checksum mappings
    2. Raw data files in data/raw/ directory
"""

import hashlib
import json
import sys
from pathlib import Path

from utils import get_logger, setup_logging, set_deterministic_seed

# Set deterministic seed for reproducibility (FR-008)
set_deterministic_seed(42)

# Setup logging
logger = setup_logging()

RAW_DATA_DIR = Path("data/raw")
MANIFEST_PATH = RAW_DATA_DIR / "manifest.json"

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except Exception as e:
        raise IOError(f"Could not compute checksum for {file_path}: {e}")

def load_manifest(manifest_path: Path) -> dict:
    """Load checksum manifest from JSON file."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
    
    with open(manifest_path, "r") as f:
        return json.load(f)

def verify_checksums(manifest: dict, data_dir: Path) -> dict:
    """
    Verify checksums of all files in the manifest.
    
    Returns:
        dict: Verification results with 'passed', 'failed', 'missing', and 'errors' lists
    """
    results = {
        "passed": [],
        "failed": [],
        "missing": [],
        "errors": []
    }
    
    for filename, expected_checksum in manifest.items():
        file_path = data_dir / filename
        
        if not file_path.exists():
            results["missing"].append(filename)
            logger.warning(f"File missing: {filename}")
            continue
        
        try:
            actual_checksum = compute_sha256(file_path)
            
            if actual_checksum == expected_checksum:
                results["passed"].append(filename)
                logger.info(f"Checksum verified: {filename}")
            else:
                results["failed"].append({
                    "filename": filename,
                    "expected": expected_checksum,
                    "actual": actual_checksum
                })
                logger.error(f"Checksum mismatch: {filename}")
        
        except Exception as e:
            results["errors"].append({
                "filename": filename,
                "error": str(e)
            })
            logger.error(f"Error processing {filename}: {e}")
    
    return results

def print_summary(results: dict):
    """Print a summary of verification results."""
    total = len(results["passed"]) + len(results["failed"]) + len(results["missing"]) + len(results["errors"])
    passed = len(results["passed"])
    failed = len(results["failed"])
    missing = len(results["missing"])
    errors = len(results["errors"])
    
    print("\n" + "=" * 50)
    print("CHECKSUM VERIFICATION SUMMARY")
    print("=" * 50)
    print(f"Total files checked: {total}")
    if total > 0:
        print(f"Passed: {passed} ({passed/total*100:.1f}%)")
    else:
        print("Passed: 0")
    print(f"Failed: {failed}")
    print(f"Missing: {missing}")
    print(f"Errors: {errors}")
    print("=" * 50)
    
    if results["failed"]:
        print("\nFailed checksums:")
        for item in results["failed"]:
            print(f"  - {item['filename']}")
            print(f"    Expected: {item['expected']}")
            print(f"    Actual:   {item['actual']}")
    
    if results["missing"]:
        print("\nMissing files:")
        for filename in results["missing"]:
            print(f"  - {filename}")
    
    if results["errors"]:
        print("\nProcessing errors:")
        for item in results["errors"]:
            print(f"  - {item['filename']}: {item['error']}")
    
    print("=" * 50)

def main():
    """Main entry point for checksum verification."""
    logger.info("Starting checksum verification")
    
    # Check if manifest exists
    if not MANIFEST_PATH.exists():
        logger.error(f"Manifest file not found: {MANIFEST_PATH}")
        print(f"Error: Manifest file not found at {MANIFEST_PATH}")
        print("Please create a manifest.json file in data/raw/ with expected checksums.")
        sys.exit(1)
    
    # Check if raw data directory exists
    if not RAW_DATA_DIR.exists():
        logger.error(f"Raw data directory not found: {RAW_DATA_DIR}")
        print(f"Error: Raw data directory not found at {RAW_DATA_DIR}")
        sys.exit(1)
    
    try:
        # Load manifest
        logger.info(f"Loading manifest from {MANIFEST_PATH}")
        manifest = load_manifest(MANIFEST_PATH)
        
        if not manifest:
            logger.warning("Manifest is empty")
            print("Warning: Manifest file is empty.")
            sys.exit(0)
        
        # Verify checksums
        logger.info(f"Verifying {len(manifest)} files")
        results = verify_checksums(manifest, RAW_DATA_DIR)
        
        # Print summary
        print_summary(results)
        
        # Exit with appropriate code
        if results["failed"] or results["errors"]:
            logger.error("Checksum verification failed")
            sys.exit(1)
        elif results["missing"]:
            logger.warning("Some files are missing")
            sys.exit(0)  # Missing files are warnings, not failures
        else:
            logger.info("Checksum verification completed successfully")
            sys.exit(0)
    
    except Exception as e:
        logger.error(f"Fatal error during verification: {e}")
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()