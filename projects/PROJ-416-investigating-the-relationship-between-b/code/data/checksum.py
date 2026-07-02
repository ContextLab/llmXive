"""
Checksum utilities for data integrity verification.
"""
import hashlib
import logging
from pathlib import Path
from typing import Optional, Dict

def compute_sha256(file_path: Path, chunk_size: int = 8192) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(chunk_size), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: Path, expected_hash: str) -> bool:
    """Verify a file's SHA256 against an expected hash."""
    actual_hash = compute_sha256(file_path)
    return actual_hash == expected_hash

def generate_checksum_manifest(directory: Path, output_path: Optional[Path] = None) -> Dict[str, str]:
    """Generate a manifest of SHA256 hashes for all files in a directory."""
    manifest = {}
    for file_path in directory.rglob("*"):
        if file_path.is_file():
            relative_path = file_path.relative_to(directory)
            manifest[str(relative_path)] = compute_sha256(file_path)
    
    if output_path:
        import json
        with open(output_path, 'w') as f:
            json.dump(manifest, f, indent=2)
    
    return manifest
