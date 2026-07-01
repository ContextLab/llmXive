import os
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional

from config import get_data_root

CHECKSUM_FILE = "checksums.json"

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_checksums() -> Dict[str, str]:
    """Load existing checksums from disk."""
    data_root = get_data_root()
    checksum_path = data_root / CHECKSUM_FILE
    if checksum_path.exists():
        with open(checksum_path, "r") as f:
            return json.load(f)
    return {}

def save_checksums(checksums: Dict[str, str]) -> None:
    """Save checksums to disk."""
    data_root = get_data_root()
    checksum_path = data_root / CHECKSUM_FILE
    with open(checksum_path, "w") as f:
        json.dump(checksums, f, indent=2)

def update_checksum_for_file(file_path: Path) -> None:
    """Compute and store checksum for a specific file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    rel_path = str(file_path.relative_to(get_data_root()))
    checksums = load_checksums()
    checksums[rel_path] = compute_file_checksum(file_path)
    save_checksums(checksums)

def verify_file_integrity(file_path: Path) -> bool:
    """Verify file integrity against stored checksum."""
    if not file_path.exists():
        return False
    
    rel_path = str(file_path.relative_to(get_data_root()))
    checksums = load_checksums()
    
    if rel_path not in checksums:
        return False
    
    current_checksum = compute_file_checksum(file_path)
    return current_checksum == checksums[rel_path]

def setup_data_environment() -> None:
    """
    Setup the data directory structure and initialize checksum tracking.
    Creates: data/raw, data/processed, data/results
    Initializes: data/checksums.json
    """
    data_root = get_data_root()
    
    # Define required subdirectories
    required_dirs = [
        data_root / "raw",
        data_root / "processed",
        data_root / "results"
    ]
    
    # Create directories if they don't exist
    for dir_path in required_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize checksum file if it doesn't exist
    checksum_path = data_root / CHECKSUM_FILE
    if not checksum_path.exists():
        save_checksums({})
    
    # Record the checksums.json file itself (optional, but good practice)
    # Note: We skip recording the checksums.json file itself to avoid circularity
    
if __name__ == "__main__":
    setup_data_environment()
    print("Data environment setup complete.")
    print(f"Root: {get_data_root()}")
    print(f"Directories created: raw, processed, results")
    print(f"Checksum tracking initialized at: {get_data_root() / CHECKSUM_FILE}")