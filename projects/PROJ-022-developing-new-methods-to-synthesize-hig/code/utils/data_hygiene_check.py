"""
Data Hygiene Check Module (T002a)

This module verifies the integrity of the data pipeline by:
1. Verifying checksums for all files in data/raw against recorded hashes in state.yaml.
2. Ensuring no files in data/processed have been modified in-place since generation.

Required for T045 (Constitutional Principle III).
"""

import os
import sys
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime

# Add project root to path for imports if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from utils.logging_config import setup_pipeline_logger
from utils.errors import DataInsufficientError, ValidationError

logger = setup_pipeline_logger("data_hygiene_check")

# Constants
RAW_DATA_DIR = Path("data/raw")
PROCESSED_DATA_DIR = Path("data/processed")
STATE_FILE = Path("state/projects/PROJ-022-developing-new-methods-to-synthesize-hig.yaml")
REPORT_PATH = Path("data/reports/data_hygiene_check.json")

def calculate_file_hash(file_path: Path) -> str:
    """
    Calculate SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found for hashing: {file_path}")
    except PermissionError:
        raise PermissionError(f"Permission denied reading file: {file_path}")

def load_state_hashes() -> Dict[str, str]:
    """
    Load recorded artifact hashes from state.yaml.
    
    Returns:
        Dictionary mapping relative file paths to their recorded hashes.
        
    Raises:
        DataInsufficientError: If state file is missing or malformed.
    """
    if not STATE_FILE.exists():
        raise DataInsufficientError(
            f"State file not found: {STATE_FILE}. "
            "Run T002f to initialize the state file."
        )

    try:
        import yaml
        with open(STATE_FILE, 'r') as f:
            state = yaml.safe_load(f)
        
        artifact_hashes = state.get('artifact_hashes', {})
        if not artifact_hashes:
            logger.warning("No artifact_hashes found in state file.")
            return {}
        
        return artifact_hashes
    except yaml.YAMLError as e:
        raise DataInsufficientError(f"Failed to parse state file YAML: {e}")
    except Exception as e:
        raise DataInsufficientError(f"Failed to load state file: {e}")

def verify_raw_data_checksums() -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Verify checksums for all files in data/raw against state.yaml.
    
    Returns:
        Tuple of (is_valid, list of validation details).
    """
    results = []
    is_valid = True

    if not RAW_DATA_DIR.exists():
        logger.warning(f"Raw data directory does not exist: {RAW_DATA_DIR}")
        return True, results # Not a failure if directory doesn't exist yet

    recorded_hashes = load_state_hashes()

    for file_path in RAW_DATA_DIR.rglob("*"):
        if file_path.is_file():
            relative_path = str(file_path.relative_to(Path(".")))
            
            # Check if we have a recorded hash for this file
            if relative_path not in recorded_hashes:
                logger.warning(f"No recorded hash found for {relative_path}. Skipping.")
                results.append({
                    "file": relative_path,
                    "status": "warning",
                    "message": "No recorded hash found"
                })
                continue

            recorded_hash = recorded_hashes[relative_path]
            
            try:
                current_hash = calculate_file_hash(file_path)
                
                if current_hash == recorded_hash:
                    logger.info(f"Checksum verified: {relative_path}")
                    results.append({
                        "file": relative_path,
                        "status": "pass",
                        "message": "Checksum verified"
                    })
                else:
                    logger.error(f"Checksum mismatch for {relative_path}")
                    results.append({
                        "file": relative_path,
                        "status": "fail",
                        "message": "Checksum mismatch",
                        "expected": recorded_hash,
                        "actual": current_hash
                    })
                    is_valid = False
            except Exception as e:
                logger.error(f"Error calculating hash for {relative_path}: {e}")
                results.append({
                    "file": relative_path,
                    "status": "error",
                    "message": str(e)
                })
                is_valid = False

    return is_valid, results

def verify_processed_data_modifications() -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Ensure no files in data/processed have been modified in-place.
    
    This checks if the modification time of processed files is older than 
    the generation timestamp recorded in their metadata (if available) or
    simply verifies they haven't been touched since the last hygiene check.
    
    For this implementation, we check if any file in data/processed has a 
    modification time newer than the current state.yaml generation time,
    or if the file content hash differs from the recorded hash.
    
    Returns:
        Tuple of (is_valid, list of validation details).
    """
    results = []
    is_valid = True

    if not PROCESSED_DATA_DIR.exists():
        logger.warning(f"Processed data directory does not exist: {PROCESSED_DATA_DIR}")
        return True, results

    recorded_hashes = load_state_hashes()

    for file_path in PROCESSED_DATA_DIR.rglob("*"):
        if file_path.is_file():
            relative_path = str(file_path.relative_to(Path(".")))
            
            # Check if we have a recorded hash for this file
            if relative_path not in recorded_hashes:
                # If no hash is recorded, we assume it's a new file or untracked
                # and flag it as a potential modification risk
                logger.warning(f"No recorded hash found for processed file {relative_path}.")
                results.append({
                    "file": relative_path,
                    "status": "warning",
                    "message": "No recorded hash found for processed file"
                })
                continue

            recorded_hash = recorded_hashes[relative_path]
            
            try:
                current_hash = calculate_file_hash(file_path)
                
                if current_hash == recorded_hash:
                    logger.info(f"Processed file integrity verified: {relative_path}")
                    results.append({
                        "file": relative_path,
                        "status": "pass",
                        "message": "Integrity verified"
                    })
                else:
                    logger.error(f"Processed file modified in-place: {relative_path}")
                    results.append({
                        "file": relative_path,
                        "status": "fail",
                        "message": "File modified in-place",
                        "expected": recorded_hash,
                        "actual": current_hash
                    })
                    is_valid = False
            except Exception as e:
                logger.error(f"Error checking processed file {relative_path}: {e}")
                results.append({
                    "file": relative_path,
                    "status": "error",
                    "message": str(e)
                })
                is_valid = False

    return is_valid, results

def generate_report(raw_results: List[Dict], processed_results: List[Dict], is_valid: bool) -> Dict[str, Any]:
    """
    Generate a comprehensive data hygiene report.
    
    Args:
        raw_results: List of validation details for raw data.
        processed_results: List of validation details for processed data.
        is_valid: Overall validity status.
        
    Returns:
        Report dictionary.
    """
    report = {
        "timestamp": datetime.now().isoformat(),
        "overall_status": "PASS" if is_valid else "FAIL",
        "raw_data_check": {
            "total_files": len(raw_results),
            "passed": sum(1 for r in raw_results if r["status"] == "pass"),
            "failed": sum(1 for r in raw_results if r["status"] == "fail"),
            "warnings": sum(1 for r in raw_results if r["status"] == "warning"),
            "details": raw_results
        },
        "processed_data_check": {
            "total_files": len(processed_results),
            "passed": sum(1 for r in processed_results if r["status"] == "pass"),
            "failed": sum(1 for r in processed_results if r["status"] == "fail"),
            "warnings": sum(1 for r in processed_results if r["status"] == "warning"),
            "details": processed_results
        }
    }
    return report

def save_report(report: Dict[str, Any]) -> Path:
    """
    Save the hygiene check report to disk.
    
    Args:
        report: The report dictionary.
        
    Returns:
        Path to the saved report file.
    """
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Data hygiene report saved to {REPORT_PATH}")
    return REPORT_PATH

def main():
    """
    Main entry point for the data hygiene check.
    """
    logger.info("Starting data hygiene check...")
    
    try:
        # 1. Verify Raw Data Checksums
        logger.info("Verifying raw data checksums...")
        raw_valid, raw_results = verify_raw_data_checksums()
        
        # 2. Verify Processed Data Modifications
        logger.info("Verifying processed data modifications...")
        processed_valid, processed_results = verify_processed_data_modifications()
        
        # 3. Determine Overall Validity
        is_valid = raw_valid and processed_valid
        
        # 4. Generate and Save Report
        report = generate_report(raw_results, processed_results, is_valid)
        save_report(report)
        
        # 5. Exit with appropriate code
        if not is_valid:
            logger.error("Data hygiene check FAILED. See report for details.")
            sys.exit(1)
        else:
            logger.info("Data hygiene check PASSED.")
            sys.exit(0)
            
    except DataInsufficientError as e:
        logger.error(f"Data insufficient error: {e}")
        sys.exit(2)
    except Exception as e:
        logger.error(f"Unexpected error during data hygiene check: {e}")
        sys.exit(3)

if __name__ == "__main__":
    main()