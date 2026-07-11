"""
Data integrity utilities for raw data validation.

This module provides checksum verification functionality to ensure the
integrity of raw datasets downloaded from external sources (e.g., Zenodo).
It supports MD5 and SHA-256 algorithms and integrates with the project's
logging infrastructure for audit trails.
"""

import hashlib
import logging
from pathlib import Path
from typing import Optional, Tuple

from .logger import get_logger

# Define supported algorithms
SUPPORTED_ALGORITHMS = {"md5", "sha256", "sha512"}

def compute_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute the checksum of a file.

    Args:
        file_path: Path to the file to compute the checksum for.
        algorithm: Hash algorithm to use ('md5', 'sha256', 'sha512').

    Returns:
        Hexadecimal string of the computed checksum.

    Raises:
        ValueError: If the algorithm is not supported.
        FileNotFoundError: If the file does not exist.
    """
    if algorithm not in SUPPORTED_ALGORITHMS:
        raise ValueError(f"Unsupported algorithm: {algorithm}. Supported: {SUPPORTED_ALGORITHMS}")

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    logger = get_logger(__name__)
    logger.info(f"Computing {algorithm} checksum for {file_path}")

    hash_func = hashlib.new(algorithm)
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(8192), b""):
                hash_func.update(chunk)
    except IOError as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise

    return hash_func.hexdigest()

def verify_checksum(
    file_path: Path, expected_checksum: str, algorithm: str = "sha256"
) -> Tuple[bool, str]:
    """
    Verify the checksum of a file against an expected value.

    Args:
        file_path: Path to the file to verify.
        expected_checksum: The expected checksum value (hex string).
        algorithm: Hash algorithm to use for verification.

    Returns:
        A tuple of (is_valid, message) where is_valid is True if the checksum matches.

    Raises:
        ValueError: If the algorithm is not supported or checksum format is invalid.
        FileNotFoundError: If the file does not exist.
    """
    if algorithm not in SUPPORTED_ALGORITHMS:
        raise ValueError(f"Unsupported algorithm: {algorithm}. Supported: {SUPPORTED_ALGORITHMS}")

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    logger = get_logger(__name__)

    # Normalize the expected checksum (remove whitespace, handle case)
    expected_checksum = expected_checksum.strip().lower()

    try:
        computed_checksum = compute_checksum(file_path, algorithm)
    except Exception as e:
        msg = f"Checksum computation failed: {e}"
        logger.error(msg)
        return False, msg

    is_valid = computed_checksum == expected_checksum

    if is_valid:
        msg = f"Checksum verification passed for {file_path.name} ({algorithm})"
        logger.info(msg)
    else:
        msg = (
            f"Checksum verification FAILED for {file_path.name}. "
            f"Expected: {expected_checksum}, Computed: {computed_checksum}"
        )
        logger.error(msg)

    return is_valid, msg

def validate_raw_data(
    file_path: Path,
    expected_checksum: str,
    algorithm: str = "sha256",
    strict: bool = True,
) -> bool:
    """
    Validate raw data integrity with optional strict mode.

    This function performs checksum verification and logs the result for audit
    purposes. In strict mode, it raises an exception if validation fails.

    Args:
        file_path: Path to the raw data file.
        expected_checksum: Expected checksum value from the source manifest.
        algorithm: Hash algorithm to use.
        strict: If True, raise ValueError on verification failure.

    Returns:
        True if validation passes (or strict=False and validation fails).

    Raises:
        ValueError: If strict=True and checksum verification fails.
    """
    is_valid, message = verify_checksum(file_path, expected_checksum, algorithm)

    if not is_valid and strict:
        raise ValueError(message)

    return is_valid

# Pre-defined checksums for known Pantheon+ datasets
# These should be updated if the source dataset changes
PANETHEON_PLUS_CHECKSUMS = {
    "zenodo_1002345": {
        "filename": "pantheon_plus.csv",
        "sha256": "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456",
        # Placeholder - actual checksums should be retrieved from Zenodo manifest
    }
}