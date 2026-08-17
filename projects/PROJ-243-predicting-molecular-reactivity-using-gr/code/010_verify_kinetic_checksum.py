"""
Task T010e: Verify checksum (SHA-256) of data/raw/kinetic_dataset_raw.csv
against the hash stored in data/raw/checksums.json.

This script validates the integrity of the curated kinetic dataset before
ingestion into the assets directory.
"""
import os
import sys
import json
import hashlib
import logging
from typing import Dict, Optional

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_config


def setup_script_logging() -> logging.Logger:
    """Configure logging for the verification script."""
    logger = logging.getLogger("verify_kinetic_checksum")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(handler)
    return logger


def calculate_sha256(file_path: str) -> str:
    """
    Calculate the SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def load_manifest(manifest_path: str) -> Dict[str, str]:
    """
    Load the checksums manifest.

    Args:
        manifest_path: Path to the checksums.json file.

    Returns:
        Dictionary mapping file paths to their expected SHA-256 hashes.

    Raises:
        FileNotFoundError: If manifest does not exist.
        json.JSONDecodeError: If manifest is invalid JSON.
    """
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Checksum manifest not found at {manifest_path}")

    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)


def verify_checksum(
    logger: logging.Logger,
    file_path: str,
    expected_hash: str,
    relative_path_key: str
) -> bool:
    """
    Verify the SHA-256 hash of a file against an expected value.

    Args:
        logger: Logger instance.
        file_path: Absolute path to the file to verify.
        expected_hash: Expected SHA-256 hash string.
        relative_path_key: Key used in the manifest for this file.

    Returns:
        True if hashes match, False otherwise.
    """
    logger.info(f"Verifying checksum for: {file_path}")
    logger.info(f"Expected hash ({relative_path_key}): {expected_hash}")

    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return False

    try:
        actual_hash = calculate_sha256(file_path)
        logger.info(f"Actual hash ({relative_path_key}):   {actual_hash}")

        if actual_hash == expected_hash:
            logger.info(f"SUCCESS: Checksum verified for {relative_path_key}")
            return True
        else:
            logger.error(f"FAILURE: Checksum mismatch for {relative_path_key}")
            logger.error(f"  Expected: {expected_hash}")
            logger.error(f"  Actual:   {actual_hash}")
            return False
    except Exception as e:
        logger.error(f"ERROR calculating hash for {file_path}: {e}")
        return False


def verify_kinetic_checksum(logger: Optional[logging.Logger] = None) -> int:
    """
    Main verification logic for T010e.

    Returns:
        Exit code: 0 for success, 1 for failure.
    """
    if logger is None:
        logger = setup_script_logging()

    config = get_config()
    base_dir = config.get("base_dir", ".")

    # Define paths relative to base_dir
    kinetic_file_rel = "data/raw/kinetic_dataset_raw.csv"
    manifest_file_rel = "data/raw/checksums.json"

    kinetic_file_path = os.path.join(base_dir, kinetic_file_rel)
    manifest_file_path = os.path.join(base_dir, manifest_file_rel)

    logger.info("Starting kinetic dataset checksum verification (T010e)")

    # 1. Check if manifest exists
    try:
        manifest = load_manifest(manifest_file_path)
        logger.info(f"Loaded manifest from {manifest_file_path}")
    except FileNotFoundError as e:
        logger.error(f"Manifest missing: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid manifest JSON: {e}")
        return 1

    # 2. Check if the kinetic file is listed in manifest
    if kinetic_file_rel not in manifest:
        logger.error(f"File '{kinetic_file_rel}' not found in checksum manifest.")
        logger.error("Please ensure T010h has been run to populate the manifest.")
        return 1

    expected_hash = manifest[kinetic_file_rel]

    # 3. Verify the file hash
    success = verify_checksum(logger, kinetic_file_path, expected_hash, kinetic_file_rel)

    if success:
        logger.info("Verification PASSED: data/raw/kinetic_dataset_raw.csv is valid.")
        return 0
    else:
        logger.error("Verification FAILED: data/raw/kinetic_dataset_raw.csv is corrupted or modified.")
        return 1


def main():
    """Entry point for the script."""
    logger = setup_script_logging()
    exit_code = verify_kinetic_checksum(logger)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()