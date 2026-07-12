"""
checksums.py: Functions to generate and verify SHA256 checksums for data files.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Any

from .constants import DATA_DIR

CHECKSUM_FILE = DATA_DIR / ".checksums.json"

def _calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def generate_checksums(target_dir: Path | None = None) -> Dict[str, str]:
    """
    Generate checksums for all files in the target directory (default: data/).
    Returns a dictionary mapping relative paths to hashes.
    """
    if target_dir is None:
        target_dir = DATA_DIR

    checksums: Dict[str, str] = {}
    for file_path in target_dir.rglob("*"):
        if file_path.is_file() and file_path.name != ".checksums.json":
            rel_path = str(file_path.relative_to(DATA_DIR))
            checksums[rel_path] = _calculate_sha256(file_path)

    return checksums

def verify_checksums() -> bool:
    """
    Verify existing checksums against current file states.
    Returns True if all match, False otherwise.
    """
    if not CHECKSUM_FILE.exists():
        return False

    with open(CHECKSUM_FILE, "r") as f:
        stored_checksums = json.load(f)

    for rel_path, stored_hash in stored_checksums.items():
        file_path = DATA_DIR / rel_path
        if not file_path.exists():
            return False
        current_hash = _calculate_sha256(file_path)
        if current_hash != stored_hash:
            return False

    return True

def main() -> None:
    """Generate and save checksums for the data directory."""
    checksums = generate_checksums()
    with open(CHECKSUM_FILE, "w") as f:
        json.dump(checksums, f, indent=2)
    print(f"Checksums saved to {CHECKSUM_FILE}")

if __name__ == "__main__":
    main()
