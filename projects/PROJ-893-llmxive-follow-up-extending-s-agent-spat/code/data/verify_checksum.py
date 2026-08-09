"""
verify_checksum.py

Implements the checksum verification gate for the downloaded S-Agent-300K dataset.
This script enforces Constitution Principle III by validating the integrity of
data artifacts against a manifest before any extraction or processing occurs.

It fails loudly (exits with code 1) if:
  1. The manifest file is missing or unreadable.
  2. The target dataset directory is missing.
  3. Any file in the target directory has a SHA-256 hash mismatching the manifest.
  4. The target directory contains files not listed in the manifest.

Usage:
    python code/data/verify_checksum.py
"""
import os
import sys
import hashlib
import json
import yaml
from pathlib import Path

# Import shared configuration
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import Config

CONFIG = Config()
MANIFEST_PATH = CONFIG.DATA_DIR / "manifest.json"
TARGET_DIR = CONFIG.DATA_DIR / "raw"  # Assuming 'raw' is where download.py places data


def compute_sha256(file_path: Path) -> str:
    """Compute the SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise RuntimeError(f"Failed to read file {file_path} for hashing: {e}")


def load_manifest(manifest_path: Path) -> dict:
    """Load the JSON manifest containing expected checksums."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found at {manifest_path}. "
                                "Run code/data/download.py first to generate the manifest.")
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in manifest file {manifest_path}: {e}")


def verify_directory_integrity(target_dir: Path, manifest: dict) -> bool:
    """
    Verify all files in target_dir against the manifest.
    
    Returns True if all checks pass.
    Raises RuntimeError on mismatch or missing files.
    """
    if not target_dir.exists():
        raise FileNotFoundError(f"Target dataset directory not found at {target_dir}. "
                                "Run code/data/download.py to fetch the data.")

    # Build a set of expected files from the manifest
    expected_files = set(manifest.keys())
    found_files = set()

    print(f"Verifying checksums for {target_dir}...")
    print(f"Manifest contains {len(expected_files)} entries.")

    # Check every file in the target directory
    for file_path in target_dir.rglob("*"):
        if file_path.is_file():
            relative_path = file_path.relative_to(target_dir)
            rel_path_str = str(relative_path)
            found_files.add(rel_path_str)

            if rel_path_str not in expected_files:
                raise ValueError(f"Unexpected file found in {target_dir}: {rel_path_str}. "
                                 "This file is not in the manifest.")

            expected_hash = manifest[rel_path_str]
            actual_hash = compute_sha256(file_path)

            if actual_hash != expected_hash:
                raise ValueError(
                    f"CHECKSUM MISMATCH for {rel_path_str}:\n"
                    f"  Expected: {expected_hash}\n"
                    f"  Actual:   {actual_hash}\n"
                    f"  Path:     {file_path}\n"
                    f"  ACTION:   Delete the corrupted data and re-run download.py."
                )
            print(f"  [OK] {rel_path_str}")

    # Ensure no expected files are missing
    missing_files = expected_files - found_files
    if missing_files:
        raise FileNotFoundError(
            f"Missing files in {target_dir} (not found in directory):\n"
            f"  {missing_files}\n"
            f"  ACTION:   Re-run download.py to ensure complete fetch."
        )

    return True


def main():
    """Entry point for the verification script."""
    try:
        manifest = load_manifest(MANIFEST_PATH)
        verify_directory_integrity(TARGET_DIR, manifest)
        
        print("\n" + "="*60)
        print("VERIFICATION SUCCESSFUL")
        print(f"All {len(manifest)} files in {TARGET_DIR} match the manifest.")
        print("Data integrity confirmed. Proceeding to extraction/processing.")
        print("="*60)
        return 0
    
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        print("\n" + "="*60)
        print("VERIFICATION FAILED")
        print(str(e))
        print("="*60)
        return 1


if __name__ == "__main__":
    sys.exit(main())