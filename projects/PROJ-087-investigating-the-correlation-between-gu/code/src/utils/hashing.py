"""
Utility module for content hashing operations.
Provides functions to compute SHA-256 hashes of files for integrity verification.
"""
import hashlib
from pathlib import Path
from typing import Union


def compute_sha256(file_path: Union[str, Path]) -> str:
    """
    Compute the SHA-256 hash of a file's contents.

    Reads the file in binary mode and computes the hash in chunks to handle
    large files efficiently without loading the entire file into memory.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string representation of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IsADirectoryError: If the path points to a directory instead of a file.
        PermissionError: If the file cannot be read due to permissions.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if path.is_dir():
        raise IsADirectoryError(f"Path is a directory, not a file: {file_path}")

    sha256_hash = hashlib.sha256()

    # Read in chunks to handle large files efficiently
    chunk_size = 8192  # 8 KB chunks
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256_hash.update(chunk)

    return sha256_hash.hexdigest()
