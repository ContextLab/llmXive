import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Any, List

from config import get_path, ensure_directories
from utils import load_json_file, save_json_file

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def generate_checksums(file_paths: List[Path]) -> Dict[str, str]:
    """Generate checksums for a list of file paths."""
    checksums = {}
    for path in file_paths:
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        checksum = compute_file_checksum(path)
        checksums[str(path)] = checksum
    return checksums

def save_checksums(checksums: Dict[str, str], output_path: Path) -> None:
    """Save checksums to a JSON file."""
    ensure_directories([output_path.parent])
    save_json_file(checksums, output_path)

def main() -> None:
    """Generate checksums for raw data files and save to data/checksums.json."""
    raw_dir = get_path("data/raw")
    output_path = get_path("data/checksums.json")

    # Collect all files in raw directory
    file_paths = [p for p in raw_dir.iterdir() if p.is_file()]

    if not file_paths:
        print("No files found in data/raw/ directory.")
        return

    print(f"Generating checksums for {len(file_paths)} files...")
    checksums = generate_checksums(file_paths)
    save_checksums(checksums, output_path)
    print(f"Checksums saved to {output_path}")

if __name__ == "__main__":
    main()
