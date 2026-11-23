"""
Utility functions for content hashing and checksum management.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union

def compute_file_hash(file_path: Union[str, Path], algorithm: str = "sha256") -> str:
    """
    Compute the hash of a file.
    
    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm (default: sha256).
    
    Returns:
        Hex digest of the file hash.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hasher = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def compute_directory_hash(dir_path: Union[str, Path], algorithm: str = "sha256") -> str:
    """
    Compute a combined hash of all files in a directory.
    
    Args:
        dir_path: Path to the directory.
        algorithm: Hash algorithm.
    
    Returns:
        Hex digest of the directory hash.
    """
    dir_path = Path(dir_path)
    if not dir_path.is_dir():
        raise NotADirectoryError(f"Not a directory: {dir_path}")
    
    hasher = hashlib.new(algorithm)
    # Sort files for deterministic ordering
    files = sorted(dir_path.rglob("*"))
    for file_path in files:
        if file_path.is_file():
            # Include relative path in hash to ensure structure matters
            rel_path = str(file_path.relative_to(dir_path))
            hasher.update(rel_path.encode('utf-8'))
            file_hash = compute_file_hash(file_path, algorithm)
            hasher.update(file_hash.encode('utf-8'))
    
    return hasher.hexdigest()

def save_checksums(checksums: Dict[str, str], output_path: Union[str, Path]):
    """Save checksums to a JSON file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(checksums, f, indent=2)

def load_checksums(input_path: Union[str, Path]) -> Dict[str, str]:
    """Load checksums from a JSON file."""
    input_path = Path(input_path)
    if not input_path.exists():
        return {}
    with open(input_path, 'r') as f:
        return json.load(f)

def verify_file_hash(file_path: Union[str, Path], expected_hash: str, algorithm: str = "sha256") -> bool:
    """Verify a file's hash against an expected value."""
    computed = compute_file_hash(file_path, algorithm)
    return computed == expected_hash

def verify_directory_checksums(dir_path: Union[str, Path], checksums_file: Union[str, Path]) -> bool:
    """Verify all files in a directory against a checksums file."""
    checksums = load_checksums(checksums_file)
    dir_path = Path(dir_path)
    for file_name, expected_hash in checksums.items():
        file_path = dir_path / file_name
        if not file_path.exists():
            return False
        if not verify_file_hash(file_path, expected_hash):
            return False
    return True

def main():
    """Test hashing utilities."""
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"test data")
        tmp_path = tmp.name
    
    try:
        h = compute_file_hash(tmp_path)
        print(f"Hash: {h}")
    finally:
        os.unlink(tmp_path)

if __name__ == "__main__":
    main()
