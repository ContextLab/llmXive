"""Utility functions for file integrity verification."""
import hashlib
from pathlib import Path

def compute_file_hash(file_path: str | Path, algorithm: str = "sha256") -> str:
    """Compute the cryptographic hash of a file.

    Parameters
    ----------
    file_path : str or Path
        Path to the file to hash.
    algorithm : str
        Hash algorithm to use (default "sha256").

    Returns
    -------
    str
        The hexadecimal digest of the file.
    """
    hash_func = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def verify_file(file_path: str | Path, expected_hash: str, algorithm: str = "sha256") -> bool:
    """Verify that a file matches the expected hash.

    Returns
    -------
    bool
        True if hashes match, False otherwise.
    """
    try:
        actual_hash = compute_file_hash(file_path, algorithm)
        return actual_hash.lower() == expected_hash.lower()
    except Exception:
        return False
