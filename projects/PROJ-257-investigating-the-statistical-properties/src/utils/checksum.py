"""
Utility functions for computing and verifying file checksums.
"""
import hashlib
from pathlib import Path
from typing import Union

def compute_file_hash(file_path: Union[str, Path], algorithm: str = "sha256") -> str:
    """
    Compute the cryptographic hash of a file.

    Parameters
    ----------
    file_path : Union[str, Path]
        Path to the file.
    algorithm : str
        Hashing algorithm to use (default 'sha256').

    Returns
    -------
    str
        The hex digest of the file.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found for checksum: {path}")

    hash_func = hashlib.new(algorithm)
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def verify_file(file_path: Union[str, Path], expected_hash: str, algorithm: str = "sha256") -> bool:
    """
    Verify that a file matches the expected hash.

    Parameters
    ----------
    file_path : Union[str, Path]
        Path to the file.
    expected_hash : str
        The expected hex digest.
    algorithm : str
        Hashing algorithm to use (default 'sha256').

    Returns
    -------
    bool
        True if hashes match, False otherwise.
    """
    try:
        actual_hash = compute_file_hash(file_path, algorithm=algorithm)
        return actual_hash == expected_hash
    except Exception:
        return False
