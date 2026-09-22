"""
Data hygiene utilities for checksums.

Implements Constitution Principle III: Data Hygiene.
"""
import hashlib
from pathlib import Path
from typing import Optional


def compute_file_checksum(filepath: Path, algorithm: str = "sha256") -> str:
    """
    Compute the checksum of a file.

    Args:
        filepath: Path to the file.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hexadecimal digest of the file.
    """
    if algorithm == "sha256":
        hasher = hashlib.sha256()
    elif algorithm == "md5":
        hasher = hashlib.md5()
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")

    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)

    return hasher.hexdigest()


def verify_file_checksum(
    filepath: Path,
    expected_checksum: str,
    algorithm: str = "sha256"
) -> bool:
    """
    Verify that a file's checksum matches the expected value.

    Args:
        filepath: Path to the file.
        expected_checksum: Expected checksum value.
        algorithm: Hash algorithm to use.

    Returns:
        True if checksums match, False otherwise.
    """
    actual_checksum = compute_file_checksum(filepath, algorithm)
    return actual_checksum == expected_checksum
