#!/usr/bin/env python3
"""
Directory setup and verification utilities for the project.

This module provides functions to create, verify, and manage the project's
directory structure, including checksum generation and verification.
"""
import os
import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Required directories
REQUIRED_DIRS = [
    "code",
    "tests",
    "data",
    "data/processed",
    "results",
    "results/benchmarks",
    "tools",
    "specs",
]

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def setup_directories() -> List[Path]:
    """Create all required directories if they don't exist."""
    created = []
    for dir_path in REQUIRED_DIRS:
        full_path = PROJECT_ROOT / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(full_path)
            print(f"Created directory: {full_path}")
    return created

def generate_checksums() -> Dict[str, str]:
    """Generate checksums for all files in data/ and results/ directories."""
    checksums = {}
    directories = [PROJECT_ROOT / "data", PROJECT_ROOT / "results"]
    
    for directory in directories:
        if directory.exists():
            for file_path in directory.rglob("*"):
                if file_path.is_file() and file_path.name != "checksums.manifest":
                    rel_path = str(file_path.relative_to(PROJECT_ROOT))
                    checksums[rel_path] = compute_file_checksum(file_path)
    
    # Save to manifest
    manifest_path = PROJECT_ROOT / "data" / "checksums.manifest"
    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write("# SHA-256 checksums for data and results files\n")
        f.write("# Format: <checksum>  <relative_path>\n")
        for rel_path, checksum in sorted(checksums.items()):
            f.write(f"{checksum}  {rel_path}\n")
    
    print(f"Generated checksums manifest: {manifest_path}")
    return checksums

def verify_directories() -> Tuple[bool, List[str]]:
    """Verify that all required directories exist and checksums are valid."""
    errors = []
    
    # Check directories
    for dir_path in REQUIRED_DIRS:
        full_path = PROJECT_ROOT / dir_path
        if not full_path.exists():
            errors.append(f"Missing directory: {full_path}")
    
    # Check checksums if manifest exists
    manifest_path = PROJECT_ROOT / "data" / "checksums.manifest"
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "  " in line:
                    expected_checksum, rel_path = line.split("  ", 1)
                    file_path = PROJECT_ROOT / rel_path
                    if file_path.exists():
                        actual_checksum = compute_file_checksum(file_path)
                        if actual_checksum != expected_checksum:
                            errors.append(f"Checksum mismatch for {rel_path}")
                    else:
                        errors.append(f"Missing file: {rel_path}")
    else:
        errors.append("Checksum manifest not found")
    
    return len(errors) == 0, errors

def main() -> int:
    """Main entry point for directory setup and verification."""
    print("Setting up project directories...")
    setup_directories()
    
    print("\nGenerating checksums...")
    generate_checksums()
    
    print("\nVerifying directories and checksums...")
    success, errors = verify_directories()
    
    if not success:
        print("\nVerification failed:")
        for error in errors:
            print(f"  - {error}")
        return 1
    
    print("\nAll checks passed.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
