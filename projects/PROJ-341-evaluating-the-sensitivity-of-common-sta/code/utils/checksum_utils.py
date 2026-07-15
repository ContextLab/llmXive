"""
Checksum utility module for verifying data integrity.

This module provides functions to compute and verify SHA-256 checksums
for files in the data directory, ensuring data hygiene (Constitution Principle III).
"""
import os
import hashlib
import json
from typing import Dict, Optional, List
from datetime import datetime


def compute_file_checksum(file_path: str) -> str:
    """
    Compute SHA-256 checksum of a file.

    Args:
        file_path: Path to the file

    Returns:
        Hexadecimal string of the SHA-256 hash
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def verify_checksum(file_path: str, expected_checksum: str) -> bool:
    """
    Verify a file's checksum against an expected value.

    Args:
        file_path: Path to the file
        expected_checksum: Expected SHA-256 hash

    Returns:
        True if checksum matches, False otherwise
    """
    if not os.path.exists(file_path):
        return False
    actual_checksum = compute_file_checksum(file_path)
    return actual_checksum == expected_checksum


def scan_directory_for_checksums(directory: str) -> Dict[str, str]:
    """
    Scan a directory and compute checksums for all files.

    Args:
        directory: Path to the directory

    Returns:
        Dictionary mapping file paths to their checksums
    """
    checksums = {}
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(('.csv', '.json', '.parquet', '.pkl')):
                file_path = os.path.join(root, file)
                checksums[file_path] = compute_file_checksum(file_path)
    return checksums


def main():
    """Main entry point for checksum utility."""
    data_dirs = ["data/raw", "data/simulation"]
    all_checksums = {}

    for directory in data_dirs:
        if os.path.exists(directory):
            print(f"Scanning {directory}...")
            checksums = scan_directory_for_checksums(directory)
            all_checksums.update(checksums)

    # Output results
    if all_checksums:
        print("\nChecksums:")
        for path, checksum in all_checksums.items():
            print(f"  {path}: {checksum}")
    else:
        print("No files found to checksum.")

    return all_checksums


if __name__ == "__main__":
    main()