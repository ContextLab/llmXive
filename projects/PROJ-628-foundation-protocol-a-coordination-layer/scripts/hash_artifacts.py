#!/usr/bin/env python3
"""
Generate SHA-256 checksums for all files in `data/` and `code/`
and write to `state/artifact_hashes.json`.

This script supports reproducibility verification for the Foundation Protocol project.
It scans the specified directories, computes SHA-256 hashes for every file,
and stores the results in a JSON manifest.
"""

import hashlib
import json
import os
import sys
from pathlib import Path

# Project root is assumed to be the parent of 'code' and 'data' directories.
# If run from the project root, this works directly.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

TARGET_DIRS = ["code", "data"]
OUTPUT_FILE = PROJECT_ROOT / "state" / "artifact_hashes.json"

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except (IOError, OSError) as e:
        print(f"Warning: Could not read file {file_path}: {e}", file=sys.stderr)
        return None

def scan_directory(directory: Path) -> dict:
    """Scan a directory and return a dict of relative_path -> sha256_hash."""
    hashes = {}
    if not directory.exists():
        print(f"Warning: Directory {directory} does not exist. Skipping.", file=sys.stderr)
        return hashes

    for root, _, files in os.walk(directory):
        for file in files:
            file_path = Path(root) / file
            # Skip the output file itself if it's in the target directory
            if file_path == OUTPUT_FILE:
                continue

            rel_path = file_path.relative_to(PROJECT_ROOT)
            file_hash = compute_sha256(file_path)
            if file_hash:
                hashes[str(rel_path)] = file_hash

    return hashes

def main():
    """Main entry point."""
    print(f"Scanning directories: {[str(d) for d in TARGET_DIRS]}")
    
    all_hashes = {}
    for dir_name in TARGET_DIRS:
        target_dir = PROJECT_ROOT / dir_name
        dir_hashes = scan_directory(target_dir)
        all_hashes.update(dir_hashes)

    # Ensure state directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Write to JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_hashes, f, indent=2, sort_keys=True)

    print(f"Successfully wrote {len(all_hashes)} hashes to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()