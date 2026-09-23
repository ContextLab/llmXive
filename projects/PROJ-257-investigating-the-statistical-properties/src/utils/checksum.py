"""
Checksum utilities for data integrity verification.

Provides SHA256 verification for downloaded files to ensure data integrity
throughout the pipeline.
"""

import hashlib
from pathlib import Path
from typing import Optional


def verify_file(path: str, expected_hash: str) -> bool:
    """
    Verify the SHA256 checksum of a file against an expected hash.

    Args:
        path: Path to the file to verify.
        expected_hash: Expected SHA256 hash string (hexadecimal).

    Returns:
        True if the file's SHA256 hash matches the expected hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the expected_hash format is invalid.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    # Validate expected hash format (64 hex characters for SHA256)
    expected_hash = expected_hash.lower().strip()
    if len(expected_hash) != 64 or not all(c in '0123456789abcdef' for c in expected_hash):
        raise ValueError(
            f"Invalid SHA256 hash format. Expected 64 hex characters, got: {expected_hash}"
        )

    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            # Read in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(8192), b''):
                sha256_hash.update(chunk)
    except IOError as e:
        raise IOError(f"Failed to read file {path}: {e}")

    computed_hash = sha256_hash.hexdigest()

    if computed_hash != expected_hash:
        return False

    return True


def compute_file_hash(path: str, algorithm: str = 'sha256') -> str:
    """
    Compute the hash of a file using the specified algorithm.

    Args:
        path: Path to the file.
        algorithm: Hash algorithm to use ('sha256', 'sha512', 'md5').

    Returns:
        Hexadecimal hash string.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if algorithm == 'sha256':
        hasher = hashlib.sha256()
    elif algorithm == 'sha512':
        hasher = hashlib.sha512()
    elif algorithm == 'md5':
        hasher = hashlib.md5()
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}. Use 'sha256', 'sha512', or 'md5'.")

    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
    except IOError as e:
        raise IOError(f"Failed to read file {path}: {e}")

    return hasher.hexdigest()
