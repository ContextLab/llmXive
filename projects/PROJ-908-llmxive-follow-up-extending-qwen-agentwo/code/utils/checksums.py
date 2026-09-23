import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)

def compute_file_sha256(file_path: Union[str, Path]) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compute_string_sha256(data: str) -> str:
    """Compute SHA256 checksum of a string."""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def verify_file_checksum(file_path: Union[str, Path], expected_checksum: str) -> bool:
    """Verify a file's checksum against an expected value."""
    actual = compute_file_sha256(file_path)
    return actual.lower() == expected_checksum.lower()

def generate_checksum_manifest(file_paths: List[Union[str, Path]]) -> Dict[str, str]:
    """Generate a manifest of checksums for a list of files."""
    manifest = {}
    for path in file_paths:
        p = Path(path)
        if p.exists():
            manifest[p.name] = compute_file_sha256(p)
        else:
            logger.warning(f"File not found for checksum: {p}")
    return manifest

def verify_checksum_manifest(manifest: Dict[str, str], directory: Union[str, Path]) -> bool:
    """Verify files in a directory against a checksum manifest."""
    directory = Path(directory)
    all_valid = True
    for filename, expected in manifest.items():
        file_path = directory / filename
        if file_path.exists():
            if not verify_file_checksum(file_path, expected):
                logger.error(f"Checksum mismatch for {file_path}")
                all_valid = False
        else:
            logger.error(f"File missing for checksum verification: {file_path}")
            all_valid = False
    return all_valid

def check_code_drift(source_path: Union[str, Path], reference_checksum: str) -> bool:
    """Check if a source file has drifted from a reference checksum."""
    if not Path(source_path).exists():
        return False
    current = compute_file_sha256(source_path)
    return current == reference_checksum
