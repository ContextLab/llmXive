"""
Checksum verification utility for raw data integrity.

This module verifies the integrity of raw data files by comparing their
computed SHA-256 checksums against a recorded hash manifest.

Usage:
    python code/utils/checksum_verify.py

Expects:
    - A manifest file at `data/raw/.checksums.txt` containing lines of:
      <sha256_hash>  <relative_file_path>
    - The raw data files themselves in `data/raw/`.

Output:
    Prints verification status to stdout.
    Returns exit code 0 if all pass, 1 if any fail or errors occur.
"""
import hashlib
import os
import sys
from pathlib import Path

MANIFEST_PATH = Path("data/raw/.checksums.txt")
RAW_DATA_DIR = Path("data/raw")

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except (IOError, OSError) as e:
        raise RuntimeError(f"Failed to read file {file_path}: {e}")

def load_manifest(manifest_path: Path) -> dict:
    """Load checksum manifest into a dictionary."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"Checksum manifest not found: {manifest_path}")
    
    checksums = {}
    with open(manifest_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            parts = line.split()
            if len(parts) != 2:
                raise ValueError(
                    f"Invalid manifest format at line {line_num}: expected '<hash>  <path>', got '{line}'"
                )
            
            hash_value, rel_path = parts
            # Validate hash format
            if len(hash_value) != 64 or not all(c in "0123456789abcdef" for c in hash_value.lower()):
                raise ValueError(f"Invalid SHA-256 hash at line {line_num}: {hash_value}")
            
            checksums[rel_path] = hash_value.lower()
    
    return checksums

def verify_checksums():
    """Verify all raw data files against the manifest."""
    if not RAW_DATA_DIR.exists():
        print("ERROR: Raw data directory does not exist.", file=sys.stderr)
        return False

    if not MANIFEST_PATH.exists():
        print("ERROR: Checksum manifest file not found.", file=sys.stderr)
        return False

    try:
        expected_checksums = load_manifest(MANIFEST_PATH)
    except (FileNotFoundError, ValueError) as e:
        print(f"ERROR: Failed to load manifest: {e}", file=sys.stderr)
        return False

    if not expected_checksums:
        print("WARNING: Manifest is empty. No files to verify.", file=sys.stderr)
        return True

    all_passed = True
    verified_count = 0
    failed_count = 0

    print(f"Verifying {len(expected_checksums)} files in {RAW_DATA_DIR}...")
    print("-" * 60)

    for rel_path, expected_hash in expected_checksums.items():
        file_path = RAW_DATA_DIR / rel_path
        
        if not file_path.exists():
            print(f"[FAIL] File missing: {rel_path}")
            all_passed = False
            failed_count += 1
            continue

        try:
            actual_hash = compute_sha256(file_path)
        except RuntimeError as e:
            print(f"[ERROR] {rel_path}: {e}")
            all_passed = False
            failed_count += 1
            continue

        if actual_hash == expected_hash:
            print(f"[PASS] {rel_path}")
            verified_count += 1
        else:
            print(f"[FAIL] {rel_path}")
            print(f"  Expected: {expected_hash}")
            print(f"  Actual:   {actual_hash}")
            all_passed = False
            failed_count += 1

    print("-" * 60)
    print(f"Summary: {verified_count} passed, {failed_count} failed.")

    return all_passed

def main():
    """Entry point for the script."""
    success = verify_checksums()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
