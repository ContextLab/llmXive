"""
code/utils/checksum.py

Utility functions for generating and verifying SHA-256 checksums.
Used to ensure data integrity for raw artifacts (Constitution Principle III).
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Union, Optional

def calculate_checksum(file_path: Union[str, Path]) -> str:
    """
    Calculate the SHA-256 checksum of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Cannot calculate checksum: File not found - {path}")

    with open(path, "rb") as f:
        # Read in chunks to handle large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    return sha256_hash.hexdigest()

def verify_checksum(file_path: Union[str, Path], expected_checksum: str) -> bool:
    """
    Verify a file's checksum against an expected value.

    Args:
        file_path: Path to the file.
        expected_checksum: The expected SHA-256 hex string.

    Returns:
        True if checksums match, False otherwise.
    """
    actual_checksum = calculate_checksum(file_path)
    return actual_checksum == expected_checksum

def generate_checksum_manifest(file_paths: list[Path], manifest_path: Path) -> None:
    """
    Generate a JSON manifest of checksums for a list of files.

    Args:
        file_paths: List of file paths to checksum.
        manifest_path: Path where the manifest JSON will be saved.
    """
    manifest = {}
    for fp in file_paths:
        if fp.exists():
            manifest[fp.name] = calculate_checksum(fp)
        else:
            manifest[fp.name] = "MISSING"

    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)

def load_checksum_manifest(manifest_path: Path) -> dict:
    """
    Load a checksum manifest from a JSON file.

    Args:
        manifest_path: Path to the manifest JSON.

    Returns:
        Dictionary mapping filenames to checksums.
    """
    if not manifest_path.exists():
        return {}
    
    with open(manifest_path, 'r', encoding='utf-8') as f:
        return json.load(f)
