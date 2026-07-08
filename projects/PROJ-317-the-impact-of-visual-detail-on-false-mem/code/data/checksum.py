import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Optional, Union

def compute_file_checksum(file_path: Union[str, Path], algorithm: str = "sha256") -> str:
    """Compute checksum for a single file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    hash_func = hashlib.new(algorithm)
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def compute_checksums_for_directory(dir_path: Union[str, Path], algorithm: str = "sha256") -> Dict[str, str]:
    """Compute checksums for all files in a directory."""
    path = Path(dir_path)
    checksums = {}
    for file_path in path.rglob('*'):
        if file_path.is_file():
            rel_path = file_path.relative_to(path)
            checksums[str(rel_path)] = compute_file_checksum(file_path, algorithm)
    return checksums

def verify_checksum(file_path: Union[str, Path], expected_checksum: str, algorithm: str = "sha256") -> bool:
    """Verify a file's checksum against expected value."""
    actual = compute_file_checksum(file_path, algorithm)
    return actual == expected_checksum

def save_checksum_manifest(checksums: Dict[str, str], output_path: Union[str, Path]):
    """Save checksums to a manifest file."""
    with open(output_path, 'w') as f:
        json.dump(checksums, f, indent=2)

def load_checksum_manifest(manifest_path: Union[str, Path]) -> Dict[str, str]:
    """Load checksums from a manifest file."""
    with open(manifest_path, 'r') as f:
        return json.load(f)

def verify_directory_integrity(dir_path: Union[str, Path], manifest_path: Union[str, Path]) -> bool:
    """Verify directory integrity against manifest."""
    manifest = load_checksum_manifest(manifest_path)
    base_path = Path(dir_path)
    for rel_path, expected_checksum in manifest.items():
        file_path = base_path / rel_path
        if not file_path.exists():
            return False
        if not verify_checksum(file_path, expected_checksum):
            return False
    return True