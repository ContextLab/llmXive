import hashlib
from pathlib import Path
from typing import Optional

def compute_file_checksum(file_path: str, algorithm: str = "sha256") -> str:
    """Compute checksum of a file."""
    hash_func = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def verify_file_checksum(file_path: str, expected_checksum: str, algorithm: str = "sha256") -> bool:
    """Verify file checksum against expected value."""
    actual_checksum = compute_file_checksum(file_path, algorithm)
    return actual_checksum == expected_checksum
