"""
Checksum utilities for data integrity verification.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from config import DATA_DIR

def compute_sha256(file_path: Path) -> str:
    """Computes the SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def generate_checksums(data_dir: Path) -> Dict[str, str]:
    """Generates checksums for all files in a directory."""
    checksums = {}
    for file_path in data_dir.rglob("*"):
        if file_path.is_file():
            relative_path = file_path.relative_to(data_dir)
            checksums[str(relative_path)] = compute_sha256(file_path)
    return checksums

def save_checksums(checksums: Dict[str, str], output_path: Path):
    """Saves checksums to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(checksums, f, indent=2)

def load_checksums(input_path: Path) -> Dict[str, str]:
    """Loads checksums from a JSON file."""
    with open(input_path, 'r') as f:
        return json.load(f)

def verify_checksums(data_dir: Path, checksums_path: Path) -> bool:
    """Verifies file checksums against a saved manifest."""
    stored_checksums = load_checksums(checksums_path)
    current_checksums = generate_checksums(data_dir)
    
    for file_path, stored_hash in stored_checksums.items():
        full_path = data_dir / file_path
        if not full_path.exists():
            print(f"Missing file: {full_path}")
            return False
        if compute_sha256(full_path) != stored_hash:
            print(f"Checksum mismatch for {file_path}")
            return False
    return True

def main():
    """Main function to generate and save checksums."""
    checksums_path = DATA_DIR / "checksums.json"
    checksums = generate_checksums(DATA_DIR)
    save_checksums(checksums, checksums_path)
    print(f"Checksums saved to {checksums_path}")

if __name__ == "__main__":
    main()
