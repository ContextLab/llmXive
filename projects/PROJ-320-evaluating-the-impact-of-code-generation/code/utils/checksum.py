"""
Checksum utilities for data integrity.

Provides SHA-256 calculation and verification for raw data artifacts.
Implements Constitution Principle III: Data Integrity via Checksumming.
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Union, Optional, List, Dict


def calculate_checksum(file_path: Union[str, Path]) -> str:
    """
    Calculate SHA-256 checksum of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def verify_checksum(file_path: Union[str, Path], expected_checksum: str) -> bool:
    """
    Verify the checksum of a file against an expected value.

    Args:
        file_path: Path to the file.
        expected_checksum: Expected SHA-256 hex string.

    Returns:
        True if checksum matches, False otherwise.
    """
    actual_checksum = calculate_checksum(file_path)
    return actual_checksum.lower() == expected_checksum.lower()


def generate_checksum_manifest(file_paths: List[Union[str, Path]], manifest_path: Union[str, Path]) -> None:
    """
    Generate a JSON manifest of checksums for multiple files.

    Args:
        file_paths: List of file paths.
        manifest_path: Path to save the JSON manifest.
    """
    manifest = {}
    for fp in file_paths:
        fp = Path(fp)
        if fp.exists():
            manifest[fp.name] = calculate_checksum(fp)
        else:
            manifest[fp.name] = "MISSING"

    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)


def load_checksum_manifest(manifest_path: Union[str, Path]) -> Dict[str, str]:
    """
    Load a checksum manifest from a JSON file.

    Args:
        manifest_path: Path to the manifest file.

    Returns:
        Dictionary mapping filenames to checksums.
    """
    with open(manifest_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    """CLI entry point for checksum utilities."""
    import sys
    if len(sys.argv) < 3:
        print("Usage: python -m utils.checksum <command> <file_or_dir>")
        print("Commands: calculate, verify")
        sys.exit(1)

    command = sys.argv[1]
    target = sys.argv[2]

    if command == "calculate":
        path = Path(target)
        if path.is_file():
            print(f"SHA-256: {calculate_checksum(path)}")
        elif path.is_dir():
            print(f"Manifest for directory {target}:")
            for f in path.iterdir():
                if f.is_file():
                    print(f"  {f.name}: {calculate_checksum(f)}")
        else:
            print(f"Error: {target} is not a file or directory.")
            sys.exit(1)

    elif command == "verify":
        # Expect format: file_path expected_checksum
        if len(sys.argv) < 4:
            print("Usage: python -m utils.checksum verify <file_path> <expected_checksum>")
            sys.exit(1)
        expected = sys.argv[3]
        path = Path(target)
        if verify_checksum(path, expected):
            print(f"Checksum verified for {target}.")
        else:
            print(f"Checksum MISMATCH for {target}.")
            sys.exit(1)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
