"""
Hashing utilities for content checksumming.
Implements T004.
"""
import hashlib
import os
from pathlib import Path
from typing import Union, Optional

def compute_file_hash(file_path: Union[str, Path]) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compute_string_hash(s: str) -> str:
    """Compute SHA256 hash of a string."""
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def verify_file_hash(file_path: Union[str, Path], expected_hash: str) -> bool:
    """Verify if a file's hash matches the expected hash."""
    return compute_file_hash(file_path) == expected_hash

def generate_manifest(file_paths: list) -> dict:
    """Generate a manifest of file paths and their hashes."""
    return {str(p): compute_file_hash(p) for p in file_paths}

def load_manifest(manifest_path: Union[str, Path]) -> dict:
    """Load a manifest from a JSON file."""
    import json
    with open(manifest_path, 'r') as f:
        return json.load(f)
