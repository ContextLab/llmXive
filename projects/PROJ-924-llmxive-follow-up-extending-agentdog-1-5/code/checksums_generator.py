"""
Checksum Generator Module for llmXive Project.

This module provides utilities to compute, generate, and save file checksums
for data integrity tracking in the raw data directory.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Any, List

from config import get_path, ensure_directories


def compute_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute the checksum of a single file.

    Args:
        file_path: Path to the file to compute the checksum for.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hexadecimal string of the checksum.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hash_func = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files efficiently
        for chunk in iter(lambda: f.read(8192), b""):
            hash_func.update(chunk)

    return hash_func.hexdigest()


def generate_checksums(raw_data_dir: Path) -> Dict[str, str]:
    """
    Generate checksums for all files in the raw data directory.

    Args:
        raw_data_dir: Path to the raw data directory.

    Returns:
        Dictionary mapping relative file paths to their checksums.

    Raises:
        FileNotFoundError: If the raw data directory does not exist.
    """
    if not raw_data_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_data_dir}")

    checksums = {}

    for file_path in raw_data_dir.iterdir():
        if file_path.is_file():
            relative_path = file_path.name
            checksum = compute_file_checksum(file_path)
            checksums[relative_path] = checksum

    return checksums


def save_checksums(checksums: Dict[str, str], output_path: Path) -> None:
    """
    Save checksums to a JSON file.

    Args:
        checksums: Dictionary of checksums to save.
        output_path: Path to the output JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2)


def main() -> None:
    """
    Main function to generate and save checksums for raw data.
    """
    # Get paths from config
    raw_data_dir = get_path("data_raw")
    checksums_output_path = get_path("data_checksums")

    # Ensure directories exist
    ensure_directories([raw_data_dir.parent])

    print(f"Generating checksums for files in: {raw_data_dir}")

    if not raw_data_dir.exists():
        print(f"Warning: Raw data directory does not exist: {raw_data_dir}")
        print("Creating empty checksums.json")
        save_checksums({}, checksums_output_path)
        return

    try:
        checksums = generate_checksums(raw_data_dir)

        if not checksums:
            print("No files found in raw data directory.")
            print("Creating empty checksums.json")

        save_checksums(checksums, checksums_output_path)
        print(f"Checksums saved to: {checksums_output_path}")
        print(f"Total files checksummed: {len(checksums)}")

        for file_name, checksum in checksums.items():
            print(f"  {file_name}: {checksum}")

    except Exception as e:
        print(f"Error generating checksums: {e}")
        raise


if __name__ == "__main__":
    main()
