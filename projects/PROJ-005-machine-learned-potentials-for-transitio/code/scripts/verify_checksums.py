"""
Script to verify SHA256 checksums of files in code/data/raw/
against stored values in code/data/raw/checksums.json.
"""
import hashlib
import json
import sys
import logging
from pathlib import Path
from src.data.checksum_manager import (
    get_project_root,
    load_checksum_manifest,
    verify_all_files
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Entry point for checksum verification.
    Loads the manifest, verifies all files, and exits with appropriate code.
    """
    project_root = get_project_root()
    checksum_file = project_root / "data/raw/checksums.json"

    if not checksum_file.exists():
        logger.error(f"Checksum manifest not found at {checksum_file}")
        sys.exit(1)

    logger.info(f"Loading checksum manifest from {checksum_file}")
    try:
        manifest = load_checksum_manifest(checksum_file)
    except Exception as e:
        logger.error(f"Failed to load manifest: {e}")
        sys.exit(1)

    logger.info(f"Found {len(manifest)} files to verify.")
    
    # Verify all files
    results = verify_all_files(manifest, project_root / "data/raw")
    
    all_valid = True
    for file_path, (expected_hash, actual_hash, is_valid) in results.items():
        status = "OK" if is_valid else "MISMATCH"
        logger.info(f"{status}: {file_path}")
        if not is_valid:
            all_valid = False
            logger.warning(f"  Expected: {expected_hash}")
            logger.warning(f"  Actual:   {actual_hash}")

    if all_valid:
        logger.info("All checksums verified successfully.")
        sys.exit(0)
    else:
        logger.error("Checksum verification failed for one or more files.")
        sys.exit(1)

if __name__ == "__main__":
    main()
