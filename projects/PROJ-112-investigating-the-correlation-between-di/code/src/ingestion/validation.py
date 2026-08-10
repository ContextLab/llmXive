import hashlib
import json
import logging
import os
import re
from pathlib import Path
from typing import Optional, Dict, Any

from src.utils.logger import get_logger
from src.ingestion.logging_config import (
    log_validation_result,
    log_download_status
)

# PII patterns
PII_PATTERNS = [
    r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
    r'\b\d{10,}\b',             # Phone numbers
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
    r'\b(?:\d{4}[- ]?){3}\d{4}\b',  # Credit card
    r'\b(?:\d{3}[- ]?){2}\d{4}\b',  # SSN variant
]

def calculate_file_checksum(file_path: str) -> str:
    """
    Calculate SHA256 checksum of a file.
    
    Args:
        file_path: Path to file
        
    Returns:
        SHA256 checksum string
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def scan_for_pii(content: str) -> list:
    """
    Scan content for PII patterns.
    
    Args:
        content: String content to scan
        
    Returns:
        List of PII matches found
    """
    matches = []
    for pattern in PII_PATTERNS:
        found = re.findall(pattern, content)
        matches.extend(found)
    return matches

def validate_no_pii(file_path: str) -> bool:
    """
    Validate that a file contains no PII.
    
    Args:
        file_path: Path to file
        
    Returns:
        True if no PII found, False otherwise
    """
    logger = get_logger(LOG_VALIDATION)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        pii_matches = scan_for_pii(content)
        
        if pii_matches:
            log_validation_result(
                logger,
                "pii_check",
                False,
                f"Found {len(pii_matches)} potential PII matches"
            )
            return False
        
        log_validation_result(logger, "pii_check", True)
        return True
        
    except Exception as e:
        log_validation_result(logger, "pii_check", False, str(e))
        return False

def record_checksums(file_paths: list, output_path: str) -> Dict[str, str]:
    """
    Record checksums for files.
    
    Args:
        file_paths: List of file paths
        output_path: Path to save checksum record
        
    Returns:
        Dictionary of file paths to checksums
    """
    logger = get_logger(LOG_VALIDATION)
    checksums = {}
    
    for file_path in file_paths:
        if os.path.exists(file_path):
            checksum = calculate_file_checksum(file_path)
            checksums[file_path] = checksum
            logger.info(f"Recorded checksum for {file_path}: {checksum[:16]}...")
        else:
            logger.warning(f"File not found: {file_path}")
    
    # Save checksums
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(checksums, f, indent=2)
    
    log_validation_result(logger, "checksum_record", True, f"Recorded {len(checksums)} checksums")
    return checksums

def validate_and_record(input_files: list, output_dir: str) -> bool:
    """
    Validate files and record checksums.
    
    Args:
        input_files: List of input file paths
        output_dir: Directory to save validation records
        
    Returns:
        True if all validations passed
    """
    logger = get_logger(LOG_VALIDATION)
    all_passed = True
    
    # Create output directory
    output_path = Path(output_dir) / "validation_records.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Validate each file for PII
    for file_path in input_files:
        if os.path.exists(file_path):
            if not validate_no_pii(file_path):
                all_passed = False
                logger.error(f"PII validation failed for {file_path}")
        else:
            all_passed = False
            logger.error(f"File not found: {file_path}")
    
    # Record checksums
    if all_passed:
        checksums = record_checksums(input_files, str(output_path))
        log_validation_result(logger, "validation_complete", True)
    else:
        log_validation_result(logger, "validation_complete", False, "PII detected or files missing")
    
    return all_passed

def main():
    """Main entry point for validation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate and record checksums for data files")
    parser.add_argument(
        "--input-files",
        type=str,
        nargs='+',
        required=True,
        help="List of input files to validate"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="state/",
        help="Directory to save validation records"
    )
    
    args = parser.parse_args()
    
    logger = get_logger(LOG_VALIDATION)
    logger.info("Starting validation process")
    
    success = validate_and_record(args.input_files, args.output_dir)
    
    if success:
        print("Validation completed successfully")
    else:
        print("Validation failed - check logs for details")
        exit(1)

if __name__ == "__main__":
    main()
