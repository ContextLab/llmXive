"""
Task T015: Create `data/raw/` directory structure and save downloaded dataset checksums.

This script ensures the `data/raw/` directory exists and runs the checksum utility
(from code/data/checksums.py) to generate SHA-256 hashes for all files in that directory.
The results are saved to `state/checksums_raw.json`.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from config import get_config
from utils.logging import get_logger
from data.checksums import ensure_raw_directory, scan_and_hash_directory, save_checksums

def main():
    logger = get_logger("T015_Checksums")
    config = get_config()
    
    # Ensure data/raw directory exists
    logger.info("Ensuring data/raw/ directory structure exists...")
    raw_dir = ensure_raw_directory(config)
    
    if not raw_dir.exists():
        logger.error(f"Failed to create {raw_dir}. Exiting.")
        sys.exit(1)
        
    logger.info(f"Directory verified: {raw_dir}")
    
    # Scan and hash contents
    logger.info("Scanning and hashing files in data/raw/...")
    checksums = scan_and_hash_directory(raw_dir, logger)
    
    if not checksums:
        logger.warning("No files found in data/raw/ to checksum.")
        # Still save an empty report or a report indicating no files
        # to maintain state consistency
    else:
        logger.info(f"Found {len(checksums)} files to checksum.")
    
    # Save checksums to state/
    state_dir = config.get("state_dir", "state")
    output_path = Path(state_dir) / "checksums_raw.json"
    
    logger.info(f"Saving checksums to {output_path}...")
    save_checksums(checksums, output_path, logger)
    
    logger.info("Task T015 completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())