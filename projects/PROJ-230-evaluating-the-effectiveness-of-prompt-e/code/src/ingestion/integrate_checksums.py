"""
T015: Integrate checksum_artifacts to hash data/raw/ files before preprocessing.

This script ensures that all files in data/raw/ are hashed using the
checksum_artifacts utility before any preprocessing occurs. This satisfies
Constitution Principle III (Constitutional Integrity) by establishing a
verified baseline of raw data before transformation.

Dependencies:
  - src/utils/checksum_artifacts.py (T006)
  - data/raw/ (populated by T013)
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to path to allow imports from src.utils
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.checksum_artifacts import scan_directory, write_checksums
from src.utils.logging import get_logger

logger = get_logger(__name__)

def main():
    """
    Main entry point for T015.
    Scans data/raw/ for files, computes SHA-256 hashes, and writes
    the result to state/checksums/raw_data_checksums.json.
    """
    # Define paths relative to project root
    raw_data_dir = project_root / "data" / "raw"
    state_checksums_dir = project_root / "state" / "checksums"

    # Ensure state/checksums directory exists
    state_checksums_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directory exists: {state_checksums_dir}")

    # Check if raw data directory exists
    if not raw_data_dir.exists():
        logger.warning(f"Raw data directory does not exist: {raw_data_dir}. "
                       "Skipping checksum generation. "
                       "Please run T013 (download_datasets) first.")
        return

    # Check if raw data directory is empty
    raw_files = list(raw_data_dir.glob("*"))
    if not raw_files:
        logger.warning(f"Raw data directory is empty: {raw_data_dir}. "
                       "Skipping checksum generation. "
                       "Please run T013 (download_datasets) first.")
        return

    logger.info(f"Scanning {len(raw_files)} files in {raw_data_dir}...")

    # Scan directory and compute hashes
    # scan_directory returns a dict: {relative_path: sha256_hash}
    checksums = scan_directory(raw_data_dir)

    if not checksums:
        logger.error("No checksums generated. Something went wrong during scanning.")
        sys.exit(1)

    logger.info(f"Generated checksums for {len(checksums)} files.")

    # Define output path for checksums
    checksum_output_path = state_checksums_dir / "raw_data_checksums.json"

    # Write checksums to file
    write_checksums(checksums, checksum_output_path)

    logger.info(f"Checksums written to: {checksum_output_path}")
    logger.info("T015 integration complete. Raw data integrity verified before preprocessing.")

if __name__ == "__main__":
    # Configure basic logging for script execution if not already done
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    main()