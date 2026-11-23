"""
Helper utilities for generating SHA‑256 checksums of data artifacts.
Used by the ingestion.generate_checksums module.
"""

import hashlib
from pathlib import Path
from typing import Dict

def generate_checksum(file_path: Path) -> str:
    """
    Compute the SHA‑256 checksum of the file at ``file_path`` and return the
    hexadecimal digest.

    The function reads the file in 64 KB chunks to avoid loading large files
    entirely into memory.

    Raises:
        FileNotFoundError: If ``file_path`` does not exist.
    """
    if not file_path.is_file():
        raise FileNotFoundError(f"Cannot compute checksum – file not found: {file_path}")

    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def generate_checksums_for_directory(base_dir: Path) -> Dict[str, str]:
    """
    Walk ``base_dir`` recursively and return a mapping of relative file paths
    (POSIX style) to their SHA‑256 checksums.

    Only regular files are considered; directories are ignored.
    """
    checksums = {}
    for path in base_dir.rglob("*"):
        if path.is_file():
            rel_path = path.relative_to(base_dir).as_posix()
            checksums[rel_path] = generate_checksum(path)
    return checksums
