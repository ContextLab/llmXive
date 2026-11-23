"""
Validation utilities for the Sensitivity Analysis Pipeline.

Includes checksum verification and data schema validation.
"""

import hashlib
from pathlib import Path
from typing import Optional

def compute_file_checksum(file_path: str, algorithm: str = "md5") -> str:
    """
    Compute the checksum of a file.

    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm (default: md5).

    Returns:
        Hex digest of the file hash.
    """
    hash_func = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def verify_checksum(actual: str, expected: str, algorithm: str = "md5") -> bool:
    """
    Verify if the actual checksum matches the expected one.

    Args:
        actual: The computed checksum.
        expected: The expected checksum.
        algorithm: The algorithm used (for normalization).

    Returns:
        True if they match, False otherwise.
    """
    # Normalize case (some tools output uppercase)
    return actual.lower() == expected.lower()
