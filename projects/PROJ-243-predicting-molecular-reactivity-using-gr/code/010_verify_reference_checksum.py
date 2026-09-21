import os
import sys
import json
import hashlib
import logging
from typing import Optional

from config import get_config, ensure_directories
from utils.logging_utils import setup_logging, log_metric, log_execution_summary
from utils.checksum_manager import load_checksums

def setup_script_logging():
    """Configure logging for the checksum verification script."""
    return setup_logging("verify_reference_checksum")

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_reference_checksum(
    logger: logging.Logger,
    file_path: str,
    expected_hash: str,
    manifest_path: str
) -> bool:
    """
    Verify the SHA-256 checksum of a file against the manifest.

    Args:
        logger: Logger instance
        file_path: Path to the file to verify
        expected_hash: Expected hash (for comparison or logging)
        manifest_path: Path to the checksums.json manifest

    Returns:
        True if verification passes, False otherwise
    """
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return False

    actual_hash = calculate_sha256(file_path)
    logger.info(f"Calculated SHA-256 for {file_path}: {actual_hash}")

    # Load the manifest to get the stored hash
    try:
        checksums = load_checksums(manifest_path)
    except FileNotFoundError:
        logger.error(f"Checksum manifest not found: {manifest_path}")
        return False
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in checksum manifest: {manifest_path}")
        return False

    # Check if the file key exists in the manifest
    file_key = os.path.basename(file_path)
    if file_key not in checksums:
        logger.error(f"File '{file_key}' not found in checksum manifest.")
        logger.error(f"Available keys: {list(checksums.keys())}")
        return False

    stored_hash = checksums[file_key]
    logger.info(f"Stored hash for {file_key}: {stored_hash}")

    if actual_hash == stored_hash:
        logger.info(f"Checksum verification PASSED for {file_key}")
        return True
    else:
        logger.error(f"Checksum verification FAILED for {file_key}")
        logger.error(f"  Expected: {stored_hash}")
        logger.error(f"  Actual:   {actual_hash}")
        return False

def main():
    """Main entry point for verifying the reference substructures checksum."""
    logger = setup_script_logging()
    logger.info("Starting reference substructures checksum verification (T010b).")

    config = get_config()
    ensure_directories()

    file_path = os.path.join(config["data_raw"], "reference_substructures_raw.csv")
    manifest_path = os.path.join(config["data_raw"], "checksums.json")

    # We don't need to pass expected_hash here as we load it from the manifest
    success = verify_reference_checksum(
        logger,
        file_path,
        expected_hash="N/A",
        manifest_path=manifest_path
    )

    # Log the result
    log_metric(logger, "checksum_verification_passed", success)

    if success:
        logger.info("Task T010b completed successfully.")
        log_execution_summary(logger, "T010b", "Success", "Checksum verified")
        sys.exit(0)
    else:
        logger.error("Task T010b failed: Checksum verification did not pass.")
        log_execution_summary(logger, "T010b", "Failed", "Checksum mismatch or file missing")
        sys.exit(1)

if __name__ == "__main__":
    main()
