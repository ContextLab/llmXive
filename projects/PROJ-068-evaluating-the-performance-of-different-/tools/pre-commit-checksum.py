#!/usr/bin/env python3
"""
Pre-commit hook to verify data integrity via checksums.

This script ensures that any files in data/processed/ and results/benchmarks/
have valid checksums recorded in .checksums.json. It prevents accidental
modification of benchmark results or data files without updating the checksum registry.

Usage:
    ln -s ../../tools/pre-commit-checksum.py .git/hooks/pre-commit
"""
import os
import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Project root is two levels up from tools/
PROJECT_ROOT = Path(__file__).parent.parent
CHECKSUM_FILE = PROJECT_ROOT / ".checksums.json"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RESULTS_BENCHMARKS_DIR = PROJECT_ROOT / "results" / "benchmarks"

# Directories to monitor for checksums
MONITORED_DIRS = [DATA_PROCESSED_DIR, RESULTS_BENCHMARKS_DIR]

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
    for directory in MONITORED_DIRS:
        if directory.exists():
            for file_path in directory.rglob("*"):
                if file_path.is_file() and not file_path.name.startswith("."):
                    files.append(file_path)
    return files

def load_checksums() -> Dict[str, str]:
    """Load existing checksums from JSON file."""
    if not CHECKSUM_FILE.exists():
        return {}
    try:
        with open(CHECKSUM_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def save_checksums(checksums: Dict[str, str]) -> None:
    """Save checksums to JSON file."""
    with open(CHECKSUM_FILE, "w") as f:
        json.dump(checksums, f, indent=2, sort_keys=True)

def verify_checksums() -> Tuple[bool, List[str]]:
    """
    Verify that all tracked files match their recorded checksums.
    
    Returns:
        Tuple of (success, list of error messages)
    """
    errors = []
    current_checksums = {}
    tracked_files = get_all_tracked_files()
    stored_checksums = load_checksums()

    for file_path in tracked_files:
        relative_path = str(file_path.relative_to(PROJECT_ROOT))
        current_checksum = compute_file_checksum(file_path)
        current_checksums[relative_path] = current_checksum

        if relative_path not in stored_checksums:
            errors.append(f"Missing checksum for: {relative_path}")
        elif stored_checksums[relative_path] != current_checksum:
            errors.append(f"Checksum mismatch for: {relative_path}")
            errors.append(f"  Expected: {stored_checksums[relative_path]}")
            errors.append(f"  Found:    {current_checksum}")

    # Check for deleted files
    for stored_path in stored_checksums:
        full_path = PROJECT_ROOT / stored_path
        if not full_path.exists():
            errors.append(f"File missing but checksum exists: {stored_path}")

    # Update checksums file with current state if no errors
    if not errors:
        save_checksums(current_checksums)

    return len(errors) == 0, errors

def generate_initial_checksums() -> Tuple[bool, List[str]]:
    """
    Generate initial checksums for all files in monitored directories.
    This is used when the checksum file doesn't exist yet.
    
    Returns:
        Tuple of (success, list of messages)
    """
    messages = []
    tracked_files = get_all_tracked_files()
    
    if not tracked_files:
        messages.append("No files found in monitored directories.")
        return True, messages

    checksums = {}
    for file_path in tracked_files:
        relative_path = str(file_path.relative_to(PROJECT_ROOT))
        checksum = compute_file_checksum(file_path)
        checksums[relative_path] = checksum
        messages.append(f"Recorded checksum for: {relative_path}")

    save_checksums(checksums)
    return True, messages

def ensure_directories() -> bool:
    """Ensure monitored directories exist."""
    for directory in MONITORED_DIRS:
        directory.mkdir(parents=True, exist_ok=True)
    return True

def main() -> int:
    """Main entry point for the pre-commit hook."""
    print("Running pre-commit checksum verification...")
    
    # Ensure directories exist
    if not ensure_directories():
        print("ERROR: Failed to ensure monitored directories exist.")
        return 1

    # If checksum file doesn't exist, generate it
    if not CHECKSUM_FILE.exists():
        print("No checksum file found. Generating initial checksums...")
        success, messages = generate_initial_checksums()
        for msg in messages:
            print(f"  {msg}")
        if not success:
            print("ERROR: Failed to generate initial checksums.")
            return 1
        print("Checksum file created. Committing changes...")
        return 0

    # Verify existing checksums
    success, errors = verify_checksums()
    
    if errors:
        print("\n❌ CHECKSUM VERIFICATION FAILED")
        print("The following files have been modified or are missing:")
        for error in errors:
            print(f"  {error}")
        print("\nPlease update the checksums by running:")
        print(f"  python tools/setup_directories.py generate-checksums")
        print("Then commit the updated .checksums.json file.")
        return 1

    print("✅ All checksums verified successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
