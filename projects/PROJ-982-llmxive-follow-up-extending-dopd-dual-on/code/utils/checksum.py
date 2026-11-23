"""
Checksum utility for generating hashes of artifacts.
"""
import hashlib
import os
from typing import Optional

def compute_file_hash(filepath: str, algorithm: str = 'sha256') -> str:
    """
    Compute the hash of a file.

    Args:
        filepath: Path to the file to hash.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hex digest of the file hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    hash_func = hashlib.new(algorithm)

    with open(filepath, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b''):
            hash_func.update(chunk)

    return hash_func.hexdigest()

def compute_directory_hash(dirpath: str, algorithm: str = 'sha256') -> str:
    """
    Compute a combined hash of all files in a directory.

    Args:
        dirpath: Path to the directory.
        algorithm: Hash algorithm to use.

    Returns:
        Hex digest of the combined directory hash.
    """
    if not os.path.isdir(dirpath):
        raise NotADirectoryError(f"Directory not found: {dirpath}")

    hash_func = hashlib.new(algorithm)
    file_paths = sorted([
        os.path.join(dirpath, f)
        for f in os.listdir(dirpath)
        if os.path.isfile(os.path.join(dirpath, f))
    ])

    for filepath in file_paths:
        # Include relative path in hash to detect moves
        rel_path = os.path.relpath(filepath, dirpath)
        hash_func.update(rel_path.encode('utf-8'))

        # Include file content hash
        file_hash = compute_file_hash(filepath, algorithm)
        hash_func.update(file_hash.encode('utf-8'))

    return hash_func.hexdigest()
