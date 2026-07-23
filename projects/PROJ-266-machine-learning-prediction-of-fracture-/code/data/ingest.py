"""
Data ingestion and checksum validation infrastructure.

This module provides utilities for validating data integrity using checksums
(SHA-256) for raw images and metadata files. It ensures that data has not
been corrupted during transfer or storage.

Dependencies:
    - hashlib (standard library)
    - os (standard library)
    - json (standard library)
    - pandas (from requirements.txt)
"""

import os
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import pandas as pd


def compute_file_checksum(file_path: str) -> str:
    """
    Compute the SHA-256 checksum of a file.

    Reads the file in chunks to handle large files efficiently without
    loading the entire file into memory.

    Args:
        file_path: Absolute or relative path to the file.

    Returns:
        Hexadecimal string representation of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    sha256_hash = hashlib.sha256()
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Error reading file {file_path}: {e}")


def validate_checksum(file_path: str, expected_checksum: str) -> bool:
    """
    Validate a file against an expected checksum.

    Args:
        file_path: Path to the file to validate.
        expected_checksum: Expected SHA-256 hex string.

    Returns:
        True if the computed checksum matches the expected one.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    computed = compute_file_checksum(file_path)
    return computed == expected_checksum


def generate_checksum_manifest(directory: str, extensions: Optional[List[str]] = None) -> Dict[str, str]:
    """
    Generate a manifest of checksums for all files in a directory.

    Args:
        directory: Path to the directory to scan.
        extensions: Optional list of file extensions to include (e.g., ['.png', '.jpg']).
                   If None, all files are included.

    Returns:
        Dictionary mapping relative file paths to their SHA-256 checksums.
    """
    manifest = {}
    base_path = Path(directory)

    if not base_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    for file_path in base_path.rglob("*"):
        if file_path.is_file():
            if extensions is None or file_path.suffix.lower() in [ext.lower() for ext in extensions]:
                rel_path = str(file_path.relative_to(base_path))
                manifest[rel_path] = compute_file_checksum(str(file_path))

    return manifest


def save_checksum_manifest(manifest: Dict[str, str], output_path: str) -> None:
    """
    Save a checksum manifest to a JSON file.

    Args:
        manifest: Dictionary of file paths to checksums.
        output_path: Path where the JSON manifest should be saved.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def load_checksum_manifest(manifest_path: str) -> Dict[str, str]:
    """
    Load a checksum manifest from a JSON file.

    Args:
        manifest_path: Path to the JSON manifest file.

    Returns:
        Dictionary of file paths to checksums.
    """
    if not Path(manifest_path).exists():
        return {}

    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_dataset_integrity(
    data_dir: str,
    manifest_path: Optional[str] = None
) -> Tuple[bool, List[str]]:
    """
    Validate the integrity of a dataset against a stored manifest.

    If no manifest is provided, one is generated and saved.

    Args:
        data_dir: Path to the dataset directory.
        manifest_path: Optional path to an existing manifest. If None,
                       a new one is generated at `data_dir/.checksum_manifest.json`.

    Returns:
        Tuple of (is_valid, list_of_failed_files).
        is_valid is True if all files match their checksums.
    """
    if manifest_path is None:
        manifest_path = os.path.join(data_dir, ".checksum_manifest.json")

    # Check if manifest exists
    if not os.path.exists(manifest_path):
        # Generate new manifest
        manifest = generate_checksum_manifest(data_dir)
        save_checksum_manifest(manifest, manifest_path)
        return True, []

    # Load existing manifest
    manifest = load_checksum_manifest(manifest_path)
    if not manifest:
        return True, []

    failed_files = []
    base_path = Path(data_dir)

    for rel_path, expected_checksum in manifest.items():
        full_path = base_path / rel_path
        if not full_path.exists():
            failed_files.append(f"{rel_path} (MISSING)")
            continue

        try:
            computed = compute_file_checksum(str(full_path))
            if computed != expected_checksum:
                failed_files.append(f"{rel_path} (MISMATCH: expected {expected_checksum}, got {computed})")
        except (FileNotFoundError, IOError) as e:
            failed_files.append(f"{rel_path} (ERROR: {str(e)})")

    return len(failed_files) == 0, failed_files


def main():
    """
    CLI entry point for checksum validation.

    Usage:
        python code/data/ingest.py validate <data_dir>
        python code/data/ingest.py generate <data_dir>
    """
    import sys

    if len(sys.argv) < 3:
        print("Usage: python code/data/ingest.py <command> <data_dir>")
        print("Commands: validate, generate")
        sys.exit(1)

    command = sys.argv[1]
    data_dir = sys.argv[2]

    try:
        if command == "validate":
            is_valid, failures = validate_dataset_integrity(data_dir)
            if is_valid:
                print(f"Validation passed for {data_dir}")
            else:
                print(f"Validation failed for {data_dir}:")
                for f in failures:
                    print(f"  - {f}")
                sys.exit(1)

        elif command == "generate":
            manifest = generate_checksum_manifest(data_dir)
            manifest_path = os.path.join(data_dir, ".checksum_manifest.json")
            save_checksum_manifest(manifest, manifest_path)
            print(f"Generated checksum manifest: {manifest_path}")
            print(f"Total files: {len(manifest)}")

        else:
            print(f"Unknown command: {command}")
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()