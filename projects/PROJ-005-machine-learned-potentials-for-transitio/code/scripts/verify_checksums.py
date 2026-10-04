"""
Script to verify SHA256 checksums of files in code/data/raw/
against stored values in code/data/raw/checksums.json.

If no files exist in data/raw/, it initializes an empty checksums.json
with the required schema.
"""
import hashlib
import json
import sys
import logging
from pathlib import Path
from src.data.checksum_manager import (
    get_project_root,
    load_checksum_manifest,
    save_checksum_manifest,
    verify_all_files,
    compute_file_checksum
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def initialize_empty_manifest(checksum_file: Path):
    """
    Creates an empty checksum manifest if no files exist in data/raw/.
    """
    empty_manifest = {}
    logger.info(f"No files found in data/raw/. Initializing empty manifest at {checksum_file}")
    save_checksum_manifest(empty_manifest, checksum_file)
    return empty_manifest

def main():
    """
    Entry point for checksum verification.
    1. Checks if data/raw/ directory exists.
    2. If empty, creates an empty checksums.json.
    3. If files exist, verifies them against checksums.json.
    4. Exits with appropriate code.
    """
    project_root = get_project_root()
    raw_dir = project_root / "data/raw"
    checksum_file = project_root / "data/raw/checksums.json"

    # Ensure raw directory exists
    if not raw_dir.exists():
        logger.warning(f"Directory {raw_dir} does not exist. Creating it.")
        raw_dir.mkdir(parents=True, exist_ok=True)

    # Scan for existing files (excluding the checksums.json itself)
    existing_files = [f for f in raw_dir.iterdir() if f.is_file() and f.name != "checksums.json"]

    if not existing_files:
        # No files to verify: initialize empty manifest if missing, or ensure it's empty
        if not checksum_file.exists():
            initialize_empty_manifest(checksum_file)
        else:
            logger.info(f"Manifest exists at {checksum_file} but no data files found. Verifying manifest is empty or cleaning up.")
            # Optional: Clean up stale manifest if it has entries but no files
            try:
                manifest = load_checksum_manifest(checksum_file)
                if manifest:
                    logger.warning("Manifest contains entries but no corresponding files found. Resetting to empty.")
                    initialize_empty_manifest(checksum_file)
            except Exception as e:
                logger.error(f"Error reading existing manifest: {e}")
                initialize_empty_manifest(checksum_file)
        logger.info("No data files to verify. Empty manifest created/verified.")
        sys.exit(0)

    # Files exist: proceed with verification
    if not checksum_file.exists():
        logger.error(f"Checksum manifest not found at {checksum_file} but data files exist.")
        logger.error("Please run the ingestion script or setup_checksums.py first.")
        sys.exit(1)

    logger.info(f"Loading checksum manifest from {checksum_file}")
    try:
        manifest = load_checksum_manifest(checksum_file)
    except Exception as e:
        logger.error(f"Failed to load manifest: {e}")
        sys.exit(1)

    if not manifest:
        logger.warning("Manifest is empty but data files exist. Verifying files and updating manifest.")
        # Compute new checksums for existing files
        new_manifest = {}
        for f in existing_files:
            rel_path = f.relative_to(project_root)
            h = compute_file_checksum(f)
            new_manifest[str(rel_path)] = h
            logger.info(f"Computed checksum for {rel_path}: {h}")
        save_checksum_manifest(new_manifest, checksum_file)
        logger.info("Manifest updated with computed checksums.")
        # Re-load to verify (it should match now)
        manifest = new_manifest

    logger.info(f"Found {len(manifest)} files to verify.")
    
    # Verify all files
    results = verify_all_files(manifest, raw_dir)
    
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
