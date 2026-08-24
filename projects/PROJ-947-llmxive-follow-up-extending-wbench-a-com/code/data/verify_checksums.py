"""
Verify downloaded artifacts against data/checksums.json.

This script validates the integrity of data files by comparing their
SHA-256 hashes against the expected values stored in data/checksums.json.
It fails loudly if any checksum mismatch is detected or if a file is missing.
"""

import hashlib
import json
import os
import sys
from pathlib import Path

# Add parent directory to path to allow imports from project modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging import get_logger, fail_loudly

logger = get_logger(__name__)


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def verify_checksums(checksums_file: Path, data_dir: Path) -> bool:
    """
    Verify all files listed in checksums.json against their stored hashes.

    Args:
        checksums_file: Path to data/checksums.json
        data_dir: Root directory for data files

    Returns:
        True if all checksums match, False otherwise.

    Raises:
        FileNotFoundError: If a file listed in checksums.json is missing.
        ValueError: If a file's hash does not match the stored checksum.
    """
    if not checksums_file.exists():
        fail_loudly(f"Checksums file not found: {checksums_file}")
        return False

    with open(checksums_file, "r") as f:
        checksum_data = json.load(f)

    files_to_verify = checksum_data.get("files", {})

    if not files_to_verify:
        logger.info("No files to verify in checksums.json")
        return True

    all_valid = True

    for relative_path, expected_checksum in files_to_verify.items():
        file_path = data_dir / relative_path

        if not file_path.exists():
            error_msg = f"Missing file: {relative_path}"
            logger.error(error_msg)
            fail_loudly(error_msg)
            all_valid = False
            continue

        try:
            actual_checksum = compute_sha256(file_path)
            if actual_checksum != expected_checksum:
                error_msg = (
                    f"Checksum mismatch for {relative_path}:\n"
                    f"  Expected: {expected_checksum}\n"
                    f"  Actual:   {actual_checksum}"
                )
                logger.error(error_msg)
                fail_loudly(error_msg)
                all_valid = False
            else:
                logger.info(f"Checksum verified: {relative_path}")
        except Exception as e:
            error_msg = f"Error verifying {relative_path}: {str(e)}"
            logger.error(error_msg)
            fail_loudly(error_msg)
            all_valid = False

    return all_valid


def main():
    """Main entry point for checksum verification."""
    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / "data"
    checksums_file = data_dir / "checksums.json"

    logger.info("Starting checksum verification...")

    try:
        success = verify_checksums(checksums_file, data_dir)
        if success:
            logger.info("All checksums verified successfully.")
            sys.exit(0)
        else:
            logger.error("Checksum verification failed.")
            sys.exit(1)
    except Exception as e:
        logger.exception(f"Fatal error during checksum verification: {e}")
        fail_loudly(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
