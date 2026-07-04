"""
Checksum utility for raw data integrity.

This module provides functions to compute and verify SHA-256 checksums
for raw data files to ensure data integrity throughout the pipeline.
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Optional, Tuple

# Import from project utilities
from logging_config import get_logger, info, error, warning
from config import load_config

logger = get_logger(__name__)


def compute_sha256(file_path: Path, chunk_size: int = 8192) -> str:
    """
    Compute SHA-256 checksum of a file.

    Args:
        file_path: Path to the file to hash
        chunk_size: Size of chunks to read (default 8KB)

    Returns:
        Hexadecimal SHA-256 hash string

    Raises:
        FileNotFoundError: If the file does not exist
        IOError: If the file cannot be read
    """
    if not file_path.exists():
        error(f"File not found for checksum: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")

    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                sha256_hash.update(chunk)
    except IOError as e:
        error(f"Error reading file for checksum: {file_path}, error: {e}")
        raise

    return sha256_hash.hexdigest()


def compute_checksums_for_directory(
    directory: Path,
    extensions: Optional[list] = None,
    recursive: bool = True
) -> Dict[str, str]:
    """
    Compute checksums for all files in a directory.

    Args:
        directory: Path to the directory
        extensions: Optional list of file extensions to include (e.g., ['.csv', '.zip'])
        recursive: Whether to search subdirectories

    Returns:
        Dictionary mapping relative file paths to their SHA-256 checksums
    """
    if not directory.exists():
        error(f"Directory not found: {directory}")
        raise FileNotFoundError(f"Directory not found: {directory}")

    checksums = {}

    if recursive:
        files = list(directory.rglob("*"))
    else:
        files = list(directory.glob("*"))

    for file_path in files:
        if file_path.is_file():
            if extensions is None or file_path.suffix.lower() in extensions:
                try:
                    checksum = compute_sha256(file_path)
                    rel_path = str(file_path.relative_to(directory))
                    checksums[rel_path] = checksum
                    info(f"Computed checksum for: {rel_path}")
                except Exception as e:
                    warning(f"Failed to compute checksum for {file_path}: {e}")

    return checksums


def save_checksums(checksums: Dict[str, str], output_path: Path) -> None:
    """
    Save checksums to a JSON file.

    Args:
        checksums: Dictionary of file paths to checksums
        output_path: Path where the JSON file will be saved
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(checksums, f, indent=2)
        info(f"Saved checksums to: {output_path}")
    except IOError as e:
        error(f"Failed to save checksums to {output_path}: {e}")
        raise


def load_checksums(checksum_path: Path) -> Dict[str, str]:
    """
    Load checksums from a JSON file.

    Args:
        checksum_path: Path to the JSON file containing checksums

    Returns:
        Dictionary of file paths to checksums

    Raises:
        FileNotFoundError: If the checksum file does not exist
        json.JSONDecodeError: If the file is not valid JSON
    """
    if not checksum_path.exists():
        error(f"Checksum file not found: {checksum_path}")
        raise FileNotFoundError(f"Checksum file not found: {checksum_path}")

    try:
        with open(checksum_path, "r", encoding="utf-8") as f:
            checksums = json.load(f)
        info(f"Loaded {len(checksums)} checksums from: {checksum_path}")
        return checksums
    except json.JSONDecodeError as e:
        error(f"Invalid JSON in checksum file {checksum_path}: {e}")
        raise


def verify_checksums(
    directory: Path,
    checksum_path: Path,
    base_path: Optional[Path] = None
) -> Tuple[bool, Dict[str, str]]:
    """
    Verify file checksums against a stored checksum file.

    Args:
        directory: Path to the directory containing the files
        checksum_path: Path to the JSON file containing stored checksums
        base_path: Optional base path to resolve relative checksum paths
                  (defaults to directory)

    Returns:
        Tuple of (all_valid: bool, results: dict)
        results dict maps file paths to status ("ok", "mismatch", "missing")

    Raises:
        FileNotFoundError: If the checksum file does not exist
    """
    stored_checksums = load_checksums(checksum_path)
    base = base_path or directory
    results = {}
    all_valid = True

    for rel_path, stored_hash in stored_checksums.items():
        file_path = base / rel_path
        results[rel_path] = "missing"

        if not file_path.exists():
            warning(f"File missing during verification: {rel_path}")
            all_valid = False
            continue

        try:
            current_hash = compute_sha256(file_path)
            if current_hash == stored_hash:
                results[rel_path] = "ok"
                info(f"Checksum OK: {rel_path}")
            else:
                results[rel_path] = "mismatch"
                error(f"Checksum MISMATCH for {rel_path}")
                error(f"  Expected: {stored_hash}")
                error(f"  Got:      {current_hash}")
                all_valid = False
        except Exception as e:
            results[rel_path] = "error"
            error(f"Error verifying {rel_path}: {e}")
            all_valid = False

    return all_valid, results


def generate_checksum_for_file(file_path: Path, output_path: Path) -> str:
    """
    Generate a checksum for a single file and save it.

    Args:
        file_path: Path to the file to checksum
        output_path: Path where the checksum will be saved

    Returns:
        The computed checksum string
    """
    checksum = compute_sha256(file_path)
    checksums = {str(file_path.name): checksum}
    save_checksums(checksums, output_path)
    return checksum


def main():
    """
    Main entry point for checksum utility CLI.

    Usage:
        python code/checksums.py compute <directory> [output_file]
        python code/checksums.py verify <directory> <checksum_file>
    """
    import sys

    if len(sys.argv) < 3:
        print("Usage:")
        print("  python code/checksums.py compute <directory> [output_file]")
        print("  python code/checksums.py verify <directory> <checksum_file>")
        sys.exit(1)

    command = sys.argv[1]
    directory = Path(sys.argv[2])

    if command == "compute":
        output_file = Path(sys.argv[3]) if len(sys.argv) > 3 else directory / "checksums.json"
        info(f"Computing checksums for directory: {directory}")
        checksums = compute_checksums_for_directory(directory)
        save_checksums(checksums, output_file)
        print(f"Generated {len(checksums)} checksums saved to: {output_file}")

    elif command == "verify":
        checksum_file = Path(sys.argv[3])
        info(f"Verifying checksums for directory: {directory}")
        all_valid, results = verify_checksums(directory, checksum_file)

        ok_count = sum(1 for v in results.values() if v == "ok")
        mismatch_count = sum(1 for v in results.values() if v == "mismatch")
        missing_count = sum(1 for v in results.values() if v == "missing")
        error_count = sum(1 for v in results.values() if v == "error")

        print(f"Verification complete: {ok_count} OK, {mismatch_count} mismatch, {missing_count} missing, {error_count} errors")

        if all_valid:
            print("All checksums verified successfully.")
        else:
            print("Checksum verification FAILED.")
            for path, status in results.items():
                if status != "ok":
                    print(f"  {path}: {status}")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()