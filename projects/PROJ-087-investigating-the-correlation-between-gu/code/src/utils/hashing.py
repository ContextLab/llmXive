"""
Utility module for computing file hashes.
Used by T009 and T016 to verify artifact integrity.
"""
import hashlib
from pathlib import Path
from typing import Union

def compute_sha256(file_path: Union[str, Path], chunk_size: int = 8192) -> str:
    """
    Compute SHA-256 hash of a file.
    Reads file in chunks to handle large files efficiently.
    
    Args:
        file_path: Path to the file.
        chunk_size: Size of chunks to read.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IsADirectoryError: If the path is a directory.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if path.is_dir():
        raise IsADirectoryError(f"Path is a directory: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()
