"""
Utility functions for hashing.
"""
import hashlib
from pathlib import Path
from typing import Union

def compute_sha256(file_path: Union[str, Path]) -> str:
    """
    Compute the SHA-256 hash of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()
