"""
verify_data_integrity.py

Pre-flight check script to ensure data integrity before heavy processing.
Verifies existence of required files (EEG, gaze.tsv) and matches checksums
against manifest.yaml.
"""
import os
import sys
import hashlib
import json
import argparse
import logging
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_manifest(manifest_path: str) -> Dict[str, Any]:
    """
    Load the manifest.yaml file containing dataset metadata and checksums.

    Args:
        manifest_path: Path to the manifest.yaml file

    Returns:
        Dictionary containing manifest data

    Raises:
        FileNotFoundError: If manifest file does not exist
        yaml.YAMLError: If manifest file is not valid YAML
    """
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(
            f"Manifest file not found: {manifest_path}. "
            "Run data generation tasks first to create manifest.yaml."
        )

    with open(manifest_path, 'r') as f:
        return yaml.safe_load(f)

def calculate_file_checksum(file_path: str, algorithm: str = 'sha256', chunk_size: int = 8192) -> str:
    """
    Calculate the checksum of a file.

    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use (default: sha256)
        chunk_size: Size of chunks to read (for memory efficiency)

    Returns:
        Hexadecimal checksum string
    """
    hash_func = hashlib.new(algorithm)
    
    with open(file_path, 'rb') as f:
        while chunk := f.read(chunk_size):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()

def verify_file_exists(file_path: str, description: str = "File") -> bool:
    """
    Verify that a file exists.

    Args:
        file_path: Path to the file
        description: Human-readable description for logging

    Returns:
        True if file exists, False otherwise
    """
    if os.path.exists(file_path):
        logger.info(f"✓ {description} exists: {file_path}")
        return True
    else:
        logger.error(f"✗ {description} missing: {file_path}")
        return False

def verify_checksum(file_path: str, expected_checksum: str, algorithm: str = 'sha256') -> bool:
    """
    Verify that a file's checksum matches the expected value.

    Args:
        file_path: Path to the file
        expected_checksum: Expected checksum value
        algorithm: Hash algorithm to use (default: sha256)

    Returns:
        True if checksum matches, False otherwise
    """
    if not os.path.exists(file_path):
        logger.error(f"Cannot verify checksum - file does not exist: {file_path}")
        return False

    try:
        actual_checksum = calculate_file_checksum(file_path, algorithm)
        
        if actual_checksum.lower() == expected_checksum.lower():
            logger.info(f"✓ Checksum verified for {file_path}")
            return True
        else:
            logger.error(
                f"✗ Checksum mismatch for {file_path}\n"
                f"  Expected: {expected_checksum}\n"
                f"  Actual:   {actual_checksum}"
            )
            return False
    except Exception as e:
        logger.error(f"✗ Error verifying checksum for {file_path}: {str(e)}")
        return False

def run_integrity_checks(
    data_dir: str,
    manifest_path: str,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Run comprehensive data integrity checks.

    Args:
        data_dir: Root directory containing the dataset
        manifest_path: Path to manifest.yaml
        verbose: Enable verbose logging

    Returns:
        Dictionary containing check results
    """
    results = {
        "status": "success",
        "checks_performed": 0,
        "checks_passed": 0,
        "checks_failed": 0,
        "details": []
    }

    try:
        manifest = load_manifest(manifest_path)
        logger.info(f"Loaded manifest from {manifest_path}")
    except Exception as e:
        error_msg = f"Failed to load manifest: {str(e)}"
        logger.error(error_msg)
        results["status"] = "failed"
        results["error"] = error_msg
        return results

    # Get dataset information from manifest
    dataset_info = manifest.get("dataset", {})
    dataset_id = dataset_info.get("id", "unknown")
    version = dataset_info.get("version", "unknown")
    
    logger.info(f"Verifying integrity for dataset: {dataset_id} (v{version})")
    logger.info(f"Data directory: {data_dir}")

    # Define required files to check
    required_files = []
    
    # Check for EEG data files (various formats)
    eeg_patterns = [
        "*.edf", "*.bdf", "*.vhdr", "*.set", "*.fif", "*.cnt"
    ]
    
    # Look for EEG files in data directory
    for pattern in eeg_patterns:
        matches = list(Path(data_dir).rglob(pattern))
        required_files.extend([
            {"path": str(p), "type": "EEG", "description": f"EEG data ({pattern})"}
            for p in matches
        ])

    # Check for gaze data
    gaze_files = list(Path(data_dir).rglob("gaze.tsv"))
    if not gaze_files:
        gaze_files = list(Path(data_dir).rglob("gaze*.tsv"))
    
    required_files.extend([
        {"path": str(p), "type": "Gaze", "description": "Gaze tracking data"}
        for p in gaze_files
    ])

    # Check for behavioral/event files
    event_patterns = ["events.tsv", "events.csv", "events.json"]
    for pattern in event_patterns:
        matches = list(Path(data_dir).rglob(pattern))
        required_files.extend([
            {"path": str(p), "type": "Events", "description": f"Event data ({pattern})"}
            for p in matches
        ])

    # If no files found in data_dir, check manifest for file list
    if not required_files and "files" in manifest:
        for file_entry in manifest["files"]:
            file_path = os.path.join(data_dir, file_entry.get("path", ""))
            required_files.append({
                "path": file_path,
                "type": file_entry.get("type", "Unknown"),
                "description": file_entry.get("description", file_entry.get("path", "")),
                "expected_checksum": file_entry.get("checksum", "")
            })

    # Perform checks
    for file_info in required_files:
        file_path = file_info["path"]
        file_type = file_info["type"]
        description = file_info["description"]
        
        results["checks_performed"] += 1

        # Check 1: File existence
        exists = verify_file_exists(file_path, description)
        if not exists:
            results["checks_failed"] += 1
            results["details"].append({
                "file": file_path,
                "type": file_type,
                "check": "existence",
                "status": "failed",
                "message": f"{description} not found"
            })
            continue

        results["checks_passed"] += 1
        results["details"].append({
            "file": file_path,
            "type": file_type,
            "check": "existence",
            "status": "passed"
        })

        # Check 2: Checksum verification (if available in manifest)
        if "expected_checksum" in file_info and file_info["expected_checksum"]:
            expected_checksum = file_info["expected_checksum"]
            checksum_ok = verify_checksum(file_path, expected_checksum)
            
            results["checks_performed"] += 1
            
            if checksum_ok:
                results["checks_passed"] += 1
                results["details"].append({
                    "file": file_path,
                    "type": file_type,
                    "check": "checksum",
                    "status": "passed"
                })
            else:
                results["checks_failed"] += 1
                results["details"].append({
                    "file": file_path,
                    "type": file_type,
                    "check": "checksum",
                    "status": "failed",
                    "message": "Checksum verification failed"
                })
                results["status"] = "failed"
        else:
            if verbose:
                logger.warning(f"No checksum available for {description}: {file_path}")

    # Final status
    if results["checks_failed"] > 0:
        results["status"] = "failed"
        logger.error(f"Integrity checks FAILED: {results['checks_failed']} failures")
    else:
        results["status"] = "success"
        logger.info(f"Integrity checks PASSED: {results['checks_passed']}/{results['checks_performed']} checks")

    return results

def main():
    """Main entry point for the data integrity verification script."""
    parser = argparse.ArgumentParser(
        description="Verify data integrity before processing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python code/utils/verify_data_integrity.py --data-dir data/raw --manifest data/manifest.yaml
  python code/utils/verify_data_integrity.py --data-dir data/raw --manifest data/manifest.yaml --verbose
        """
    )
    
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data/raw",
        help="Root directory containing the dataset (default: data/raw)"
    )
    
    parser.add_argument(
        "--manifest",
        type=str,
        default="data/manifest.yaml",
        help="Path to manifest.yaml file (default: data/manifest.yaml)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default="results/integrity_report.json",
        help="Path to output report file (default: results/integrity_report.json)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()

    # Ensure output directory exists
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # Run integrity checks
    logger.info("Starting data integrity verification...")
    results = run_integrity_checks(
        data_dir=args.data_dir,
        manifest_path=args.manifest,
        verbose=args.verbose
    )

    # Write results to output file
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results written to {args.output}")

    # Exit with appropriate code
    if results["status"] == "failed":
        logger.error("Data integrity verification FAILED. Aborting pipeline.")
        sys.exit(1)
    else:
        logger.info("Data integrity verification PASSED. Ready for processing.")
        sys.exit(0)

if __name__ == "__main__":
    main()