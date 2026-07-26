"""
T009b: Verify SHA-256 checksum of reference substructures raw data.

This script verifies the integrity of `data/raw/reference_substructures_raw.csv`
against a manifest file. It ensures the data downloaded in T009a has not been
corrupted or tampered with.

Workflow:
1. Locate `data/raw/reference_substructures_raw.csv`.
2. Locate `data/raw/reference_substructures_raw.csv.sha256` (manifest).
3. Calculate SHA-256 of the CSV.
4. Compare with the manifest value.
5. Exit with code 0 on success, 1 on failure.
"""

import os
import sys
import logging
import hashlib
from typing import Optional

# Add parent directory to path for imports if running as script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_config
from utils.loaders import calculate_sha256

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_manifest(manifest_path: str) -> Optional[str]:
    """
    Reads the SHA-256 hash from the manifest file.
    Expected format: <hash>  <filename> (standard sha256sum output)
    or just <hash> if generated manually.
    """
    if not os.path.exists(manifest_path):
        logger.error(f"Manifest file not found: {manifest_path}")
        return None

    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            # Handle standard sha256sum format: "hash  filename"
            # or simple hash-only format
            parts = content.split()
            if len(parts) >= 1:
                return parts[0]
            logger.error(f"Invalid manifest content format in {manifest_path}")
            return None
    except Exception as e:
        logger.error(f"Failed to read manifest {manifest_path}: {e}")
        return None

def verify_checksum(data_path: str, manifest_path: str) -> bool:
    """
    Verifies the SHA-256 checksum of the data file against the manifest.
    Returns True if valid, False otherwise.
    """
    if not os.path.exists(data_path):
        logger.error(f"Data file not found: {data_path}")
        return False

    expected_hash = load_manifest(manifest_path)
    if expected_hash is None:
        return False

    logger.info(f"Calculating SHA-256 for {data_path}...")
    try:
        actual_hash = calculate_sha256(data_path)
    except Exception as e:
        logger.error(f"Failed to calculate hash for {data_path}: {e}")
        return False

    logger.info(f"Expected: {expected_hash}")
    logger.info(f"Actual:   {actual_hash}")

    if actual_hash == expected_hash:
        logger.info("SUCCESS: Checksum verification passed.")
        return True
    else:
        logger.error("FAILURE: Checksum mismatch. Data integrity compromised.")
        return False

def main():
    """
    Main entry point for T009b.
    """
    config = get_config()
    # Ensure we are looking at the raw directory as per T009a/T009b spec
    raw_dir = os.path.join(config.data_dir, "raw")
    filename = "reference_substructures_raw.csv"
    data_path = os.path.join(raw_dir, filename)
    manifest_path = os.path.join(raw_dir, f"{filename}.sha256")

    logger.info(f"Starting checksum verification for {filename}")
    
    success = verify_checksum(data_path, manifest_path)

    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()