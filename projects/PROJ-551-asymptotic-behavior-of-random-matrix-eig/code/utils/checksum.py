"""
Checksum utilities for data hygiene.
"""
import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Any

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compute_directory_checksums(dir_path: Path) -> Dict[str, str]:
    """Compute checksums for all files in a directory."""
    checksums = {}
    for file_path in dir_path.iterdir():
        if file_path.is_file():
            checksums[str(file_path)] = compute_file_checksum(file_path)
    return checksums

def save_checksum_manifest(checksums: Dict[str, str], output_path: Path) -> None:
    """Save checksum manifest to a JSON file."""
    with open(output_path, "w") as f:
        json.dump(checksums, f, indent=2)

def load_checksum_manifest(input_path: Path) -> Dict[str, str]:
    """Load checksum manifest from a JSON file."""
    with open(input_path, "r") as f:
        return json.load(f)

def verify_checksums(file_path: Path, expected_checksum: str) -> bool:
    """Verify that a file's checksum matches the expected value."""
    actual_checksum = compute_file_checksum(file_path)
    return actual_checksum == expected_checksum

def checksum_raw_data(data_dir: Path, registry_path: Path) -> Dict[str, Any]:
    """Compute checksums for all raw data files and register them."""
    checksums = {}
    for file_path in data_dir.iterdir():
        if file_path.is_file() and file_path.suffix == ".npy":
            checksum = compute_file_checksum(file_path)
            checksums[str(file_path)] = checksum
    
    # Register in metadata
    registry = {"entries": []}
    if registry_path.exists():
        with open(registry_path, "r") as f:
            registry = json.load(f)
    
    for file_path, checksum in checksums.items():
        registry["entries"].append({
            "file": file_path,
            "checksum": checksum,
            "algorithm": "sha256"
        })
    
    with open(registry_path, "w") as f:
        json.dump(registry, f, indent=2)
    
    return checksums

def checksum_processed_data(data_dir: Path, registry_path: Path) -> Dict[str, Any]:
    """Compute checksums for all processed data files and register them."""
    return checksum_raw_data(data_dir, registry_path)
