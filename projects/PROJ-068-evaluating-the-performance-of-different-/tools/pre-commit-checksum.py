#!/usr/bin/env python3
"""
Pre-commit hook to verify checksums of data and results files.

This script ensures that any files tracked in `data/` and `results/` 
have valid checksums recorded in `data/checksums.manifest`.

Usage:
    ln -s ../../tools/pre-commit-checksum.py .git/hooks/pre-commit
"""
import os
import sys
import subprocess
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Project root is two levels up from tools/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"
CHECKSUM_MANIFEST = PROJECT_ROOT / "data" / "checksums.manifest"

# Directories to check
DIRECTORIES_TO_CHECK = [DATA_DIR, RESULTS_DIR]

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        print(f"Error computing checksum for {file_path}: {e}", file=sys.stderr)
        raise

def load_checksums() -> Dict[str, str]:
    """Load existing checksums from manifest file."""
    checksums = {}
    if not CHECKSUM_MANIFEST.exists():
        return checksums
    
    with open(CHECKSUM_MANIFEST, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "  " in line:
                checksum, rel_path = line.split("  ", 1)
                checksums[rel_path] = checksum
    return checksums

def save_checksums(checksums: Dict[str, str]) -> None:
    """Save checksums to manifest file."""
    with open(CHECKSUM_MANIFEST, "w", encoding="utf-8") as f:
        f.write("# SHA-256 checksums for data and results files\n")
        f.write("# Format: <checksum>  <relative_path>\n")
        for rel_path, checksum in sorted(checksums.items()):
            f.write(f"{checksum}  {rel_path}\n")

def get_staged_files() -> List[Path]:
    """Get list of staged files in the data/ and results/ directories."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=True
        )
        files = [Path(f) for f in result.stdout.splitlines() if f]
        return [f for f in files if f.is_relative_to(DATA_DIR) or f.is_relative_to(RESULTS_DIR)]
    except subprocess.CalledProcessError as e:
        print(f"Error getting staged files: {e}", file=sys.stderr)
        return []

def verify_checksums() -> Tuple[bool, List[str]]:
    """Verify checksums of all files in tracked directories."""
    errors = []
    current_checksums = {}
    
    for directory in DIRECTORIES_TO_CHECK:
        if not directory.exists():
            continue
        
        for file_path in directory.rglob("*"):
            if file_path.is_file() and file_path.name != "checksums.manifest":
                rel_path = file_path.relative_to(PROJECT_ROOT)
                current_checksums[str(rel_path)] = compute_file_checksum(file_path)
    
    existing_checksums = load_checksums()
    
    # Check for missing or changed files
    all_files = set(current_checksums.keys()) | set(existing_checksums.keys())
    
    for rel_path in all_files:
        current = current_checksums.get(rel_path)
        existing = existing_checksums.get(rel_path)
        
        if current is None and existing is not None:
            errors.append(f"File deleted without updating manifest: {rel_path}")
        elif current is not None and existing is None:
            errors.append(f"New file without checksum: {rel_path}")
        elif current != existing:
            errors.append(f"Checksum mismatch for {rel_path}: expected {existing}, got {current}")
    
    return len(errors) == 0, errors

def update_manifest_for_staged_files(staged_files: List[Path]) -> None:
    """Update manifest with checksums for staged files."""
    existing_checksums = load_checksums()
    
    for file_path in staged_files:
        full_path = PROJECT_ROOT / file_path
        if full_path.exists():
          rel_path = str(file_path)
          checksum = compute_file_checksum(full_path)
          existing_checksums[rel_path] = checksum
          print(f"Updated checksum for {rel_path}")
    
    save_checksums(existing_checksums)

def main() -> int:
    """Main entry point for the pre-commit hook."""
    print("Running pre-commit checksum verification...")
    
    # Get staged files
    staged_files = get_staged_files()
    
    if staged_files:
        print(f"Found {len(staged_files)} staged files in data/ or results/")
        update_manifest_for_staged_files(staged_files)
    
    # Verify all checksums
    success, errors = verify_checksums()
    
    if not success:
        print("\nChecksum verification failed:")
        for error in errors:
            print(f"  - {error}")
        print("\nPlease update the checksums manifest or fix the files.")
        return 1
    
    print("Checksum verification passed.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
