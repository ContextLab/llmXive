"""
Utility for computing and verifying SHA-256 checksums of artifacts.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, List

def compute_string_sha256(data: str) -> str:
    """Compute SHA-256 hash of a string."""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def compute_file_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def hash_artifacts(file_paths: List[Path]) -> Dict[str, str]:
    """
    Compute hashes for a list of file paths.

    Args:
        file_paths: List of Path objects to hash.

    Returns:
        Dictionary mapping file paths to their SHA-256 hashes.
    """
    hashes = {}
    for path in file_paths:
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        hashes[str(path)] = compute_file_sha256(path)
    return hashes

def verify_artifacts(expected_hashes: Dict[str, str], file_paths: List[Path]) -> bool:
    """
    Verify that files match expected hashes.

    Args:
        expected_hashes: Dictionary mapping file paths (str) to expected hashes.
        file_paths: List of Path objects to verify.

    Returns:
        True if all files match, False otherwise.
    """
    all_valid = True
    for path in file_paths:
        path_str = str(path)
        if path_str not in expected_hashes:
            print(f"Warning: No expected hash for {path}")
            continue

        actual_hash = compute_file_sha256(path)
        expected_hash = expected_hashes[path_str]

        if actual_hash != expected_hash:
            print(f"Hash mismatch for {path}:")
            print(f"  Expected: {expected_hash}")
            print(f"  Actual:   {actual_hash}")
            all_valid = False
        else:
            print(f"Verified: {path}")

    return all_valid

def main():
    """Example usage of hash utilities."""
    import sys
    if len(sys.argv) > 1:
        file_path = Path(sys.argv[1])
        if file_path.exists():
            h = compute_file_sha256(file_path)
            print(f"SHA-256 of {file_path}: {h}")
        else:
            print(f"File not found: {file_path}")
            sys.exit(1)
    else:
        print("Usage: python hash_artifacts.py <file_path>")
        sys.exit(1)

if __name__ == "__main__":
    main()