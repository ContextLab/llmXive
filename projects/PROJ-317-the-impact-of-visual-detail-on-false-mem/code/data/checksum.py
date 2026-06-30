import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Optional, Union

def compute_file_checksum(file_path: Union[str, Path], algorithm: str = 'sha256') -> str:
    """Compute the checksum of a single file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    hasher = hashlib.new(algorithm)
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def compute_checksums_for_directory(dir_path: Union[str, Path], algorithm: str = 'sha256') -> Dict[str, str]:
    """Compute checksums for all files in a directory recursively."""
    path = Path(dir_path)
    if not path.is_dir():
        raise NotADirectoryError(f"Not a directory: {path}")
    
    checksums = {}
    for file_path in path.rglob('*'):
        if file_path.is_file():
            relative_path = file_path.relative_to(path)
            checksums[str(relative_path)] = compute_file_checksum(file_path, algorithm)
    return checksums

def verify_checksum(file_path: Union[str, Path], expected_checksum: str, algorithm: str = 'sha256') -> bool:
    """Verify a file's checksum against an expected value."""
    computed = compute_file_checksum(file_path, algorithm)
    return computed == expected_checksum

def save_checksum_manifest(checksums: Dict[str, str], output_path: Union[str, Path]):
    """Save checksums to a JSON manifest file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(checksums, f, indent=2)

def load_checksum_manifest(manifest_path: Union[str, Path]) -> Dict[str, str]:
    """Load checksums from a JSON manifest file."""
    path = Path(manifest_path)
    if not path.exists():
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def verify_directory_integrity(dir_path: Union[str, Path], manifest_path: Union[str, Path]) -> bool:
    """Verify all files in a directory against a manifest."""
    current_checksums = compute_checksums_for_directory(dir_path)
    expected_checksums = load_checksum_manifest(manifest_path)
    
    if set(current_checksums.keys()) != set(expected_checksums.keys()):
        return False
    
    for file_rel_path, expected_hash in expected_checksums.items():
        if current_checksums.get(file_rel_path) != expected_hash:
            return False
    return True