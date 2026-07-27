"""
Module: checksum

Purpose:
    Provides utilities for verifying the integrity of raw data files
    using SHA-256 checksums.

Functions:
    - verify_raw_data_integrity: Verifies a single file against a checksum.
    - generate_checksum_file: Generates a checksum file for a directory.
    - verify_all_raw_data: Verifies all files in the raw data directory.
    - main: Entry point for the script.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from utils.config import get_project_root, get_path, ensure_dir, get_config

def verify_raw_data_integrity(file_path: Path, expected_checksum: str) -> bool:
    """
    Verifies the integrity of a single file against an expected checksum.

    Args:
        file_path (Path): Path to the file.
        expected_checksum (str): Expected SHA-256 hash.

    Returns:
        bool: True if valid, False otherwise.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest() == expected_checksum

def generate_checksum_file(directory: Path, output_path: Path):
    """
    Generates a JSON file containing checksums for all files in a directory.

    Args:
        directory (Path): Directory to scan.
        output_path (Path): Path to the output JSON file.
    """
    checksums = {}
    for file_path in directory.rglob("*"):
        if file_path.is_file():
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            checksums[str(file_path.relative_to(directory))] = sha256_hash.hexdigest()

    with open(output_path, 'w') as f:
        json.dump(checksums, f, indent=2)

def verify_all_raw_data() -> Dict[str, bool]:
    """
    Verifies all files in the raw data directory against stored checksums.

    Returns:
        Dict[str, bool]: Mapping of filename to verification status.
    """
    config = get_config()
    raw_dir = get_path("raw_data_dir", "data/raw")
    checksum_file = get_path("checksums_file", "data/raw/checksums.json")

    if not checksum_file.exists():
        return {}

    with open(checksum_file, 'r') as f:
        stored_checksums = json.load(f)

    results = {}
    for filename, expected in stored_checksums.items():
        file_path = raw_dir / filename
        if file_path.exists():
            results[filename] = verify_raw_data_integrity(file_path, expected)
        else:
            results[filename] = False

    return results

def main():
    """
    Main entry point for the checksum script.

    Runs verification for all raw data files.
    """
    results = verify_all_raw_data()
    all_valid = all(results.values())
    if all_valid:
        print("All raw data files verified successfully.")
    else:
        print("Some raw data files failed verification.")
        for name, valid in results.items():
            if not valid:
                print(f"  - {name}: FAILED")

if __name__ == "__main__":
    main()
