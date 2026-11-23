"""
Task T015: Create `data/raw/` directory structure and save downloaded dataset checksums.

This script ensures the `data/raw/` directory exists (creating it if necessary)
and then invokes the checksum utility to generate SHA-256 hashes for all
files currently present in that directory, saving the manifest to `state/checksums_raw.json`.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_config
from utils.logging import get_logger
from data.checksums import ensure_raw_directory, scan_and_hash_directory, save_checksums


def main():
    """
    Main entry point for Task T015.
    1. Ensures `data/raw/` exists.
    2. Scans the directory for files.
    3. Computes SHA-256 hashes.
    4. Saves the checksum manifest to `state/checksums_raw.json`.
    """
    logger = get_logger("T015")
    logger.info("Starting Task T015: Create raw directory and generate checksums.")

    config = get_config()
    raw_dir = config.get("paths.raw_data")
    state_dir = config.get("paths.state")

    # 1. Ensure raw directory exists
    logger.info(f"Ensuring raw data directory exists: {raw_dir}")
    ensure_raw_directory(raw_dir)

    # 2. Scan and hash
    logger.info(f"Scanning directory for checksums: {raw_dir}")
    checksums = scan_and_hash_directory(raw_dir)

    if not checksums:
        logger.warning("No files found in data/raw/ to checksum. "
                       "This is expected if the download script (T010) has not been run yet. "
                       "An empty manifest will be created.")
    else:
        logger.info(f"Found {len(checksums)} files to hash.")

    # 3. Save checksums
    checksum_file_path = state_dir / "checksums_raw.json"
    logger.info(f"Saving checksum manifest to: {checksum_file_path}")
    save_checksums(checksums, checksum_file_path)

    logger.info("Task T015 completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
