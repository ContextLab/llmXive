"""
T015: Integrate checksum_artifacts to hash data/raw files before preprocessing.

This script ensures that all files in data/raw/ are hashed using the 
checksum_artifacts utility BEFORE any preprocessing occurs. This satisfies
Constitution Principle III (Traceability) and provides a verified baseline
for the raw dataset.

Usage:
    python src/ingestion/integrate_checksums.py
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path for imports if running as script
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.checksum_artifacts import scan_directory, write_checksums
from src.utils.logging import get_logger

def main():
    """
    Main entry point for T015.
    1. Locate data/raw/ directory.
    2. Scan for all files.
    3. Compute SHA-256 hashes.
    4. Write results to state/checksums/ (specifically for raw files).
    """
    logger = get_logger("integrate_checksums")
    
    # Define paths relative to project root
    raw_dir = project_root / "data" / "raw"
    checksum_dir = project_root / "state" / "checksums"
    
    if not raw_dir.exists():
        logger.warning(f"Raw data directory {raw_dir} does not exist. "
                       "Skipping checksum generation. Ensure T013 has run.")
        return

    # Ensure checksum directory exists
    checksum_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Scanning raw data directory: {raw_dir}")
    files_to_hash = list(raw_dir.glob("*"))
    
    if not files_to_hash:
        logger.warning("No files found in data/raw/ to hash.")
        return

    logger.info(f"Found {len(files_to_hash)} files to hash.")
    
    # Compute hashes
    # The scan_directory function returns a list of (path, hash) tuples
    checksums = scan_directory(raw_dir)
    
    if not checksums:
        logger.error("Failed to compute checksums for any files.")
        return

    # Write checksums to the state directory
    # We name the file specifically for the raw dataset to distinguish it
    # from processed data checksums if they are added later.
    checksum_file = checksum_dir / "raw_data_checksums.json"
    
    write_checksums(checksums, checksum_file)
    
    logger.info(f"Successfully wrote checksums to {checksum_file}")
    logger.info(f"Total files hashed: {len(checksums)}")

if __name__ == "__main__":
    main()