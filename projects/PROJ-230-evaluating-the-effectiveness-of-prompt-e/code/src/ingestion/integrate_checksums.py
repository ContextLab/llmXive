"""
Integrate checksum artifacts into the preprocessing pipeline.

This module scans the data/raw/ directory for downloaded dataset files,
computes their SHA-256 hashes using the checksum_artifacts utility,
and writes the results to state/checksums/ for provenance tracking.

This implements the requirement to hash data/raw/ files before preprocessing
(Task T015).
"""
import os
import sys
import logging
from pathlib import Path

# Import from existing API surface
from src.utils.checksum_artifacts import scan_directory, write_checksums
from src.utils.logging import get_logger

def main():
    """
    Main entry point for integrating checksums into the preprocessing pipeline.
    
    This function:
    1. Scans data/raw/ for all files
    2. Computes SHA-256 hashes for each file
    3. Writes the results to state/checksums/raw_checksums.json
    4. Logs the operation for auditability
    
    Returns:
        bool: True if successful, False otherwise
    """
    logger = get_logger(__name__)
    logger.info("Starting checksum integration for data/raw/ files")
    
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parents[2]
    raw_data_dir = project_root / "data" / "raw"
    state_dir = project_root / "state" / "checksums"
    
    # Ensure state directory exists
    state_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if raw data directory exists
    if not raw_data_dir.exists():
        logger.warning(f"Raw data directory does not exist: {raw_data_dir}")
        logger.info("Skipping checksum integration - no raw data to hash")
        return True
    
    # Scan directory for files
    logger.info(f"Scanning directory: {raw_data_dir}")
    files_info = scan_directory(raw_data_dir)
    
    if not files_info:
        logger.warning(f"No files found in {raw_data_dir}")
        return True
    
    logger.info(f"Found {len(files_info)} files to hash")
    
    # Write checksums to state directory
    output_path = state_dir / "raw_checksums.json"
    write_checksums(files_info, output_path)
    
    logger.info(f"Checksums written to: {output_path}")
    logger.info(f"Total files hashed: {len(files_info)}")
    
    # Log summary
    for file_info in files_info:
        logger.info(
            f"Hashed: {file_info['relative_path']} -> {file_info['sha256'][:16]}..."
        )
    
    logger.info("Checksum integration completed successfully")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)