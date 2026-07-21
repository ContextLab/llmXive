import hashlib
from pathlib import Path
from typing import Union

def compute_sha256(file_path: Union[str, Path]) -> str:
    """
    Compute the SHA-256 hash of a file.

    Reads the file in binary mode and computes the hash in chunks
    to handle large files efficiently without loading the entire
    file into memory.

    Args:
        file_path: Path to the file to be hashed.

    Returns:
        Hexadecimal string representation of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IsADirectoryError: If the path points to a directory.
        PermissionError: If the file cannot be read.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if path.is_dir():
        raise IsADirectoryError(f"Path is a directory, expected a file: {file_path}")

    sha256_hash = hashlib.sha256()

    # Read in chunks to handle large files efficiently (64KB chunks)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256_hash.update(chunk)

    return sha256_hash.hexdigest()
