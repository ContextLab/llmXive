import hashlib
from pathlib import Path
from typing import Union


def compute_sha256(file_path: Union[str, Path]) -> str:
    """
    Compute the SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        The hexadecimal SHA-256 hash string.

    Raises:
        FileNotFoundError: If the file does not exist.
        IsADirectoryError: If the path points to a directory.
        PermissionError: If there are permission issues reading the file.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if path.is_dir():
        raise IsADirectoryError(f"Path is a directory, expected a file: {path}")

    sha256_hash = hashlib.sha256()

    # Read in chunks to handle large files efficiently
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)

    return sha256_hash.hexdigest()
