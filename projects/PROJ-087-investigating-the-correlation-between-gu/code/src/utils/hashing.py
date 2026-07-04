import hashlib
from pathlib import Path
from typing import Union


def compute_sha256(file_path: Union[str, Path]) -> str:
    """
    Compute the SHA-256 hash of a file's contents.

    Reads the file in binary mode and updates the hash object in chunks
    to handle large files efficiently without loading the entire file into memory.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string representation of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        PermissionError: If the file cannot be read due to permissions.
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}")

    sha256_hash = hashlib.sha256()
    
    try:
        with open(path, "rb") as f:
            # Read in chunks of 8KB to handle large files efficiently
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
    except PermissionError:
        raise PermissionError(f"Permission denied reading file: {path}")

    return sha256_hash.hexdigest()