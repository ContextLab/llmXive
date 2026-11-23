"""
Utility module for hashing artifacts (files and directories) to ensure versioning discipline.
Used by T032 to generate the final artifact_hashes.yaml.
"""
import hashlib
import os
from pathlib import Path
from typing import Optional, Dict, List

def hash_file(file_path: Path) -> str:
    """
    Compute SHA-256 hash of a file's contents.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def hash_directory(dir_path: Path) -> str:
    """
    Compute a deterministic SHA-256 hash for a directory.
    This hashes the sorted list of relative paths and their individual file hashes.
    
    Args:
        dir_path: Path to the directory.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    
    # Collect all files in the directory recursively
    files = []
    for root, _, filenames in os.walk(dir_path):
        for filename in filenames:
            # Skip hidden files or specific patterns if needed
            if filename.startswith('.'):
                continue
            full_path = Path(root) / filename
            rel_path = full_path.relative_to(dir_path)
            files.append((str(rel_path), full_path))
    
    # Sort to ensure determinism regardless of filesystem order
    files.sort(key=lambda x: x[0])
    
    for rel_path_str, full_path in files:
        # Hash the relative path string
        sha256_hash.update(rel_path_str.encode('utf-8'))
        # Hash the file content
        file_hash = hash_file(full_path)
        sha256_hash.update(file_hash.encode('utf-8'))
    
    return sha256_hash.hexdigest()

def verify_file_hash(file_path: Path, expected_hash: str) -> bool:
    """
    Verify if a file's hash matches the expected hash.
    
    Args:
        file_path: Path to the file.
        expected_hash: Expected SHA-256 hex string.
        
    Returns:
        True if match, False otherwise.
    """
    if not file_path.exists():
        return False
    actual_hash = hash_file(file_path)
    return actual_hash == expected_hash

def save_hashes(hashes: Dict[str, str], output_path: Path):
    """
    Save a dictionary of hashes to a JSON file.
    (Note: T032 uses YAML, but this helper supports JSON if needed elsewhere)
    """
    import json
    with open(output_path, 'w') as f:
        json.dump(hashes, f, indent=2)

def load_hashes(input_path: Path) -> Dict[str, str]:
    """
    Load a dictionary of hashes from a JSON file.
    """
    import json
    with open(input_path, 'r') as f:
        return json.load(f)

def generate_manifest(base_dir: Path) -> Dict[str, str]:
    """
    Generate a manifest of all files in a base directory with their hashes.
    """
    manifest = {}
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.startswith('.'):
                continue
            full_path = Path(root) / file
            rel_path = full_path.relative_to(base_dir)
            manifest[str(rel_path)] = hash_file(full_path)
    return manifest

if __name__ == "__main__":
    # Simple test if run directly
    import sys
    if len(sys.argv) > 1:
        target = Path(sys.argv[1])
        if target.exists():
            if target.is_file():
                print(f"File hash: {hash_file(target)}")
            elif target.is_dir():
                print(f"Dir hash: {hash_directory(target)}")
        else:
            print(f"Path not found: {target}")
    else:
        print("Usage: python hash_artifacts.py <path>")
