"""
Checksum utilities for data integrity.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Union, Optional, List, Dict

def calculate_checksum(file_path: Union[str, Path]) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: Union[str, Path], expected_checksum: str) -> bool:
    """Verify the checksum of a file against an expected value."""
    actual = calculate_checksum(file_path)
    return actual == expected_checksum

def generate_checksum_manifest(file_paths: List[Union[str, Path]], output_path: Union[str, Path]) -> None:
    """Generate a JSON manifest of checksums for a list of files."""
    manifest = {}
    for path in file_paths:
        path_str = str(path)
        manifest[path_str] = calculate_checksum(path_str)
    
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)

def load_checksum_manifest(manifest_path: Union[str, Path]) -> Dict[str, str]:
    """Load a checksum manifest from a file."""
    with open(manifest_path, 'r') as f:
        return json.load(f)

def main():
    # Test
    pass

if __name__ == "__main__":
    main()
