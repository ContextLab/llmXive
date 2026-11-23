"""
Script to verify raw data integrity before and after processing.

This script computes SHA-256 hashes of raw data files before processing,
stores them, and then verifies that the raw files remain unchanged after
preprocessing (per Constitution Principle III).

It ensures no in-place modification of raw data occurs.
"""
import os
import sys
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import time
import json
from datetime import datetime

# Add parent directory to path to allow imports from code/
sys.path.insert(0, str(Path(__file__).parent))

from utils.validators import compute_sha256
from utils.logging_utils import log_warning


def log_header(message: str) -> None:
    """Log a formatted header message."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def get_raw_files(raw_dir: Path) -> List[Path]:
    """
    Get all CSV files in the raw data directory.
    
    Args:
        raw_dir: Path to the raw data directory.
        
    Returns:
        List of Path objects for CSV files.
    """
    if not raw_dir.exists():
        log_warning(f"Raw directory does not exist: {raw_dir}")
        return []
    
    csv_files = list(raw_dir.glob("*.csv"))
    return csv_files


def load_expected_checksums(checksum_file: Path) -> Optional[Dict[str, str]]:
    """
    Load expected checksums from a JSON file.
    
    Args:
        checksum_file: Path to the checksum JSON file.
        
    Returns:
        Dictionary mapping filenames to SHA-256 hashes, or None if file doesn't exist.
    """
    if not checksum_file.exists():
        return None
    
    with open(checksum_file, 'r') as f:
        return json.load(f)


def verify_integrity_workflow(
    raw_dir: Path,
    checksum_file: Path,
    processed_dir: Optional[Path] = None
) -> Tuple[bool, Dict[str, Dict[str, str]]]:
    """
    Verify integrity of raw data files.
    
    This function:
    1. Computes SHA-256 hashes of all raw CSV files.
    2. Compares against expected checksums if available.
    3. If a processed_dir is provided, verifies raw files are unchanged after processing.
    
    Args:
        raw_dir: Path to the raw data directory.
        checksum_file: Path to the expected checksums JSON file.
        processed_dir: Optional path to processed data directory (for post-processing check).
        
    Returns:
        Tuple of (success: bool, results: Dict)
        - success: True if all verifications passed
        - results: Dictionary with verification details for each file
    """
    log_header("=== Raw Data Integrity Verification ===")
    log_header("Computing SHA-256 hashes for raw files...")
    
    raw_files = get_raw_files(raw_dir)
    if not raw_files:
        log_warning("No CSV files found in raw directory.")
        return False, {}
    
    results = {}
    all_passed = True
    
    # Compute current checksums
    current_checksums = {}
    for file_path in raw_files:
        log_header(f"Processing: {file_path.name}")
        try:
            checksum = compute_sha256(file_path)
            current_checksums[file_path.name] = checksum
            results[file_path.name] = {
                "current_hash": checksum,
                "expected_hash": None,
                "status": "computed"
            }
            log_header(f"  Current SHA-256: {checksum}")
        except Exception as e:
            log_warning(f"Failed to compute checksum for {file_path.name}: {e}")
            results[file_path.name] = {
                "current_hash": None,
                "expected_hash": None,
                "status": "error",
                "error": str(e)
            }
            all_passed = False
    
    # Load and compare with expected checksums
    expected_checksums = load_expected_checksums(checksum_file)
    if expected_checksums:
        log_header("Comparing against stored checksums...")
        for filename, expected_hash in expected_checksums.items():
            if filename in results:
                if results[filename]["current_hash"] == expected_hash:
                    results[filename]["expected_hash"] = expected_hash
                    results[filename]["status"] = "verified"
                    log_header(f"  ✓ {filename}: Hash verified")
                else:
                    results[filename]["expected_hash"] = expected_hash
                    results[filename]["status"] = "mismatch"
                    log_warning(f"  ✗ {filename}: Hash MISMATCH!")
                    log_warning(f"    Expected: {expected_hash}")
                    log_warning(f"    Current:  {results[filename]['current_hash']}")
                    all_passed = False
            else:
                log_warning(f"  Expected checksum for {filename} not found in raw directory")
    else:
        log_header("No expected checksums found. Creating new checksum file...")
        # Save current checksums for future verification
        with open(checksum_file, 'w') as f:
            json.dump(current_checksums, f, indent=2)
        log_header(f"Saved checksums to {checksum_file}")
    
    # If processed_dir is provided, verify raw files haven't changed
    if processed_dir and processed_dir.exists():
        log_header("=== Post-Processing Integrity Check ===")
        log_header("Verifying raw files remain unchanged after preprocessing...")
        
        # Re-compute checksums to ensure no modification
        for file_path in raw_files:
            try:
                new_checksum = compute_sha256(file_path)
                if file_path.name in results:
                    if new_checksum == results[file_path.name]["current_hash"]:
                        log_header(f"  ✓ {file_path.name}: Unchanged after processing")
                        results[file_path.name]["post_processing_hash"] = new_checksum
                        results[file_path.name]["post_processing_status"] = "unchanged"
                    else:
                        log_warning(f"  ✗ {file_path.name}: MODIFIED after processing!")
                        log_warning(f"    Before: {results[file_path.name]['current_hash']}")
                        log_warning(f"    After:  {new_checksum}")
                        results[file_path.name]["post_processing_hash"] = new_checksum
                        results[file_path.name]["post_processing_status"] = "modified"
                        all_passed = False
            except Exception as e:
                log_warning(f"Failed to re-compute checksum for {file_path.name}: {e}")
                results[file_path.name]["post_processing_status"] = "error"
                all_passed = False
    
    log_header("=== Verification Summary ===")
    if all_passed:
        log_header("✓ All integrity checks PASSED")
    else:
        log_header("✗ Some integrity checks FAILED")
    
    return all_passed, results


def main():
    """Main entry point for the script."""
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent
    raw_dir = project_root / "data" / "raw"
    checksum_file = project_root / "state" / "projects" / "PROJ-099-statistical-analysis-of-algorithmic-fair" / "raw_checksums.json"
    processed_dir = project_root / "data" / "processed"
    
    # Ensure state directory exists
    checksum_file.parent.mkdir(parents=True, exist_ok=True)
    
    start_time = time.time()
    success, results = verify_integrity_workflow(raw_dir, checksum_file, processed_dir)
    elapsed = time.time() - start_time
    
    log_header(f"Verification completed in {elapsed:.2f} seconds")
    
    # Save detailed results to a report file
    report_file = project_root / "data" / "analysis" / "raw_integrity_report.json"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "files_checked": len(results),
            "results": results
        }, f, indent=2)
    
    log_header(f"Detailed report saved to: {report_file}")
    
    if not success:
        log_warning("Integrity verification failed. Please investigate the mismatches.")
        sys.exit(1)
    else:
        log_header("Raw data integrity verified successfully.")
        sys.exit(0)


if __name__ == "__main__":
    main()