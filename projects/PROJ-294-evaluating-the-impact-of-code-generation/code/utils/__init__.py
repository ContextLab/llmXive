import hashlib
import os
from typing import Optional

def compute_sha256(file_path: str) -> str:
    """
    Compute the SHA256 checksum of a file.
    Raises FileNotFoundError if the file does not exist.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found for SHA256 computation: {file_path}")
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: str, expected_hash: str) -> bool:
    """
    Verify that the SHA256 checksum of `file_path` matches `expected_hash`.
    Returns True if they match, False otherwise.
    """
    try:
        actual_hash = compute_sha256(file_path)
    except FileNotFoundError:
        return False
    return actual_hash.lower() == expected_hash.lower()
