import os
import sys
import hashlib
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from config import config

# Use the correct path from Config
MANIFEST_PATH = config.DATA_RAW / "manifest.json"

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        raise RuntimeError(f"Failed to compute hash for {file_path}: {e}")

def load_manifest() -> Dict[str, str]:
    """Load the manifest.json file."""
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Manifest not found at {MANIFEST_PATH}")
    with open(MANIFEST_PATH, "r") as f:
        return json.load(f)

def verify_directory_integrity(directory: Path, manifest: Optional[Dict[str, str]] = None) -> bool:
    """
    Verify SHA-256 checksums of all files in directory against manifest.
    Returns True if all match, False otherwise.
    """
    if manifest is None:
        manifest = load_manifest()

    all_valid = True
    for filename, expected_hash in manifest.items():
        file_path = directory / filename
        if not file_path.exists():
            print(f"Missing file: {file_path}")
            all_valid = False
            continue
        
        actual_hash = compute_sha256(file_path)
        if actual_hash != expected_hash:
            print(f"Checksum mismatch for {filename}: expected {expected_hash}, got {actual_hash}")
            all_valid = False
    
    return all_valid

def main():
    """CLI entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Verify directory checksums")
    parser.add_argument("--directory", type=str, default=str(config.DATA_RAW), help="Directory to verify")
    args = parser.parse_args()

    directory = Path(args.directory)
    if not directory.exists():
        print(f"Error: Directory {directory} does not exist.")
        sys.exit(1)

    try:
        if verify_directory_integrity(directory):
            print("Verification successful: All checksums match.")
            sys.exit(0)
        else:
            print("Verification failed: Checksum mismatches detected.")
            sys.exit(1)
    except Exception as e:
        print(f"Verification error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
