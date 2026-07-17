#!/usr/bin/env python3
"""
Pre-commit hook to verify checksums of data files in data/processed/ and results/benchmarks/.

This script ensures data integrity by verifying that all tracked data files
match their recorded checksums in the .checksums.json manifest.

Usage:
    ln -s ../../tools/pre-commit-checksum.py .git/hooks/pre-commit
"""
import os
import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Project root relative to this script
PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RESULTS_BENCHMARKS_DIR = PROJECT_ROOT / "results" / "benchmarks"
CHECKSUM_MANIFEST = PROJECT_ROOT / ".checksums.json"
EXCLUDED_PATTERNS = {".git", "__pycache__", "*.pyc", ".DS_Store", "temp_*", "tmp_*"}

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def should_exclude(path: Path) -> bool:
    """Check if a path should be excluded from checksum verification."""
    for pattern in EXCLUDED_PATTERNS:
        if pattern in path.parts or path.name.startswith(pattern.replace("*", "")):
            return True
    return False

def get_data_files(directory: Path) -> List[Path]:
    """Get all data files in a directory recursively."""
    if not directory.exists():
        return []
    files = []
    for file_path in directory.rglob("*"):
        if file_path.is_file() and not should_exclude(file_path):
            files.append(file_path)
    return files

def generate_checksums() -> Dict[str, str]:
    """Generate checksums for all data files."""
    checksums = {}
    directories_to_check = [DATA_PROCESSED_DIR, RESULTS_BENCHMARKS_DIR]
    
    for directory in directories_to_check:
        if not directory.exists():
            continue
        for file_path in get_data_files(directory):
            rel_path = file_path.relative_to(PROJECT_ROOT)
            checksum = compute_file_checksum(file_path)
            checksums[str(rel_path)] = checksum
    
    return checksums

def verify_checksums() -> Tuple[bool, List[str]]:
    """Verify current checksums against the manifest."""
    if not CHECKSUM_MANIFEST.exists():
        print("WARNING: No checksum manifest found. Generating initial manifest...")
        new_checksums = generate_checksums()
        if new_checksums:
            with open(CHECKSUM_MANIFEST, "w") as f:
                json.dump(new_checksums, f, indent=2)
            print(f"Generated checksum manifest with {len(new_checksums)} files.")
        return True, []
    
    with open(CHECKSUM_MANIFEST, "r") as f:
        manifest = json.load(f)
    
    errors = []
    current_checksums = generate_checksums()
    
    # Check for modified or missing files
    for file_path, expected_checksum in manifest.items():
        full_path = PROJECT_ROOT / file_path
        if not full_path.exists():
            errors.append(f"MISSING: {file_path}")
            continue
        
        actual_checksum = compute_file_checksum(full_path)
        if actual_checksum != expected_checksum:
            errors.append(f"MODIFIED: {file_path} (expected: {expected_checksum[:16]}..., got: {actual_checksum[:16]}...)")
    
    # Check for new files not in manifest
    for file_path in current_checksums:
        if file_path not in manifest:
            errors.append(f"NEW FILE (not tracked): {file_path}")
    
    # Update manifest if there are new files
    if any("NEW FILE" in err for err in errors):
        print("\nUpdating checksum manifest to include new files...")
        with open(CHECKSUM_MANIFEST, "w") as f:
            json.dump(current_checksums, f, indent=2)
        # Filter out new file warnings from errors
        errors = [e for e in errors if "NEW FILE" not in e]
    
    return len(errors) == 0, errors

def main() -> int:
    """Main entry point for the pre-commit hook."""
    print("Running checksum verification...")
    
    # Ensure directories exist
    for directory in [DATA_PROCESSED_DIR, RESULTS_BENCHMARKS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
    
    success, errors = verify_checksums()
    
    if errors:
        print("\n❌ CHECKSUM VERIFICATION FAILED:")
        for error in errors:
            print(f"  - {error}")
        print("\nCommit aborted. Please ensure all data files are properly tracked.")
        return 1
    
    print("✅ All data files verified successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
