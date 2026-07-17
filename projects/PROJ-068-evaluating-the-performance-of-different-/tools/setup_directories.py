#!/usr/bin/env python3
"""
Setup and verification script for project directories and checksums.

This script handles:
- Creating required directory structure
- Generating initial checksums for data files
- Verifying checksum integrity
"""
import os
import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Any

PROJECT_ROOT = Path(__file__).parent.parent
CHECKSUM_FILE = PROJECT_ROOT / ".checksums.json"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RESULTS_BENCHMARKS_DIR = PROJECT_ROOT / "results" / "benchmarks"

REQUIRED_DIRS = [
    "code",
    "tests",
    "data",
    "data/processed",
    "results",
    "results/benchmarks",
    "tools",
]

def setup_directories() -> bool:
    """Create all required directories."""
    print("Setting up project directories...")
    for dir_path in REQUIRED_DIRS:
        full_path = PROJECT_ROOT / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ {full_path}")
    return True

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return ""

def get_all_tracked_files() -> List[Path]:
    """Get all files in monitored directories."""
    files = []
    monitored_dirs = [DATA_PROCESSED_DIR, RESULTS_BENCHMARKS_DIR]
    for directory in monitored_dirs:
        if directory.exists():
            for file_path in directory.rglob("*"):
                if file_path.is_file() and not file_path.name.startswith("."):
                    files.append(file_path)
    return files

def generate_checksums() -> bool:
    """Generate checksums for all files in monitored directories."""
    print("Generating checksums for data files...")
    
    tracked_files = get_all_tracked_files()
    if not tracked_files:
        print("  No files found in monitored directories.")
        # Create empty checksum file
        with open(CHECKSUM_FILE, "w") as f:
            json.dump({}, f)
        return True

    checksums = {}
    for file_path in tracked_files:
        relative_path = str(file_path.relative_to(PROJECT_ROOT))
        checksum = compute_file_checksum(file_path)
        checksums[relative_path] = checksum
        print(f"  ✓ {relative_path}: {checksum[:16]}...")

    with open(CHECKSUM_FILE, "w") as f:
        json.dump(checksums, f, indent=2, sort_keys=True)

    print(f"Checksums saved to {CHECKSUM_FILE}")
    return True

def verify_directories() -> bool:
    """Verify that all required directories exist."""
    print("Verifying directory structure...")
    all_exist = True
    for dir_path in REQUIRED_DIRS:
        full_path = PROJECT_ROOT / dir_path
        if not full_path.exists():
            print(f"  ✗ Missing: {full_path}")
            all_exist = False
        else:
            print(f"  ✓ {full_path}")
    return all_exist

def verify_checksums() -> bool:
    """Verify checksums of all tracked files."""
    print("Verifying file checksums...")
    
    if not CHECKSUM_FILE.exists():
        print("  ⚠ No checksum file found. Run 'generate-checksums' first.")
        return False

    with open(CHECKSUM_FILE, "r") as f:
        stored_checksums = json.load(f)

    tracked_files = get_all_tracked_files()
    all_valid = True

    for file_path in tracked_files:
        relative_path = str(file_path.relative_to(PROJECT_ROOT))
        current_checksum = compute_file_checksum(file_path)
        
        if relative_path not in stored_checksums:
            print(f"  ✗ Missing checksum for: {relative_path}")
            all_valid = False
        elif stored_checksums[relative_path] != current_checksum:
            print(f"  ✗ Checksum mismatch: {relative_path}")
            print(f"      Expected: {stored_checksums[relative_path]}")
            print(f"      Found:    {current_checksum}")
            all_valid = False
        else:
            print(f"  ✓ {relative_path}")

    # Check for deleted files
    for stored_path in stored_checksums:
        full_path = PROJECT_ROOT / stored_path
        if not full_path.exists():
            print(f"  ⚠ File missing but checksum exists: {stored_path}")
            all_valid = False

    return all_valid

def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python setup_directories.py <command>")
        print("Commands:")
        print("  setup          - Create required directories")
        print("  generate-checksums - Generate checksums for data files")
        print("  verify         - Verify directory structure and checksums")
        print("  verify-dirs    - Verify only directory structure")
        print("  verify-checksums - Verify only checksums")
        sys.exit(1)

    command = sys.argv[1]

    if command == "setup":
        success = setup_directories()
    elif command == "generate-checksums":
        success = generate_checksums()
    elif command == "verify":
        dirs_ok = verify_directories()
        checksums_ok = verify_checksums()
        success = dirs_ok and checksums_ok
    elif command == "verify-dirs":
        success = verify_directories()
    elif command == "verify-checksums":
        success = verify_checksums()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
