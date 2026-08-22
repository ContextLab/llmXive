"""
Setup script for data directory structures with checksum verification.

This script:
1. Ensures `data/raw/` and `data/processed/` directories exist.
2. Implements a checksum verification mechanism for downloaded data files.
3. Logs all operations and verification results.
"""
import os
import hashlib
import logging
from pathlib import Path
import sys

# Add project root to path to allow imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import DATA_RAW_DIR, DATA_PROCESSED_DIR
from utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)


def ensure_dir(dir_path: Path) -> bool:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        dir_path: Path to the directory to ensure.

    Returns:
        True if directory exists or was created successfully, False otherwise.
    """
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Directory ensured: {dir_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {dir_path}: {e}")
        return False


def compute_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute the checksum of a file.

    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hexadecimal checksum string.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If an unsupported algorithm is specified.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if algorithm not in hashlib.algorithms_available:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")

    hasher = hashlib.new(algorithm)
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        logger.error(f"Error computing checksum for {file_path}: {e}")
        raise


def verify_checksum(
    file_path: Path,
    expected_checksum: str,
    algorithm: str = "sha256",
    raise_on_failure: bool = True
) -> bool:
    """
    Verify the checksum of a file against an expected value.

    Args:
        file_path: Path to the file to verify.
        expected_checksum: Expected checksum string.
        algorithm: Hash algorithm to use (default: sha256).
        raise_on_failure: If True, raise ValueError on mismatch.

    Returns:
        True if checksum matches, False otherwise.

    Raises:
        ValueError: If checksums do not match and raise_on_failure is True.
        FileNotFoundError: If the file does not exist.
    """
    if not file_path.exists():
        logger.error(f"File not found for checksum verification: {file_path}")
        if raise_on_failure:
            raise FileNotFoundError(f"File not found: {file_path}")
        return False

    try:
        actual_checksum = compute_file_checksum(file_path, algorithm)
        if actual_checksum.lower() == expected_checksum.lower():
            logger.info(f"Checksum verified for {file_path}: {actual_checksum[:16]}...")
            return True
        else:
            error_msg = (
                f"Checksum mismatch for {file_path}.\n"
                f"Expected: {expected_checksum}\n"
                f"Actual:   {actual_checksum}"
            )
            logger.error(error_msg)
            if raise_on_failure:
                raise ValueError(error_msg)
            return False
    except Exception as e:
        if raise_on_failure:
            raise
        logger.error(f"Checksum verification failed for {file_path}: {e}")
        return False


def main() -> int:
    """
    Main entry point for the data directory setup script.

    Returns:
        0 on success, 1 on failure.
    """
    logger.info("Starting data directory setup...")

    # Ensure required directories exist
    raw_success = ensure_dir(DATA_RAW_DIR)
    processed_success = ensure_dir(DATA_PROCESSED_DIR)

    if not (raw_success and processed_success):
        logger.error("Failed to create required data directories.")
        return 1

    logger.info("Data directory structure setup complete.")

    # Example of how to use checksum verification (commented out as no file is provided yet)
    # This demonstrates the integration point for data loaders
    # sample_file = DATA_RAW_DIR / "example.csv"
    # if sample_file.exists():
    #     verify_checksum(sample_file, "expected_checksum_here")

    return 0


if __name__ == "__main__":
    sys.exit(main())