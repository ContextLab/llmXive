"""
Checksum management for data directories.

This module provides functions to compute, store, and verify checksums
for files in data/raw/ and data/processed/ directories to ensure data
integrity and provenance tracking.
"""

import os
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from src.lib.utils import compute_file_hash, ensure_dir
from src.config import get_config


CHECKSUM_FILE_NAME = ".checksums.json"


def _get_checksum_file_path(data_dir: Path) -> Path:
    """Return the path to the checksums file for a given data directory."""
    return data_dir / CHECKSUM_FILE_NAME


def compute_directory_checksums(data_dir: Path) -> Dict[str, Dict[str, Any]]:
    """
    Compute SHA-256 checksums for all files in a directory recursively.

    Args:
        data_dir: Path to the data directory (e.g., data/raw or data/processed).

    Returns:
        A dictionary mapping relative file paths to their metadata:
        {
            "relative/path/file.csv": {
                "sha256": "abc123...",
                "size_bytes": 12345,
                "timestamp": "2023-10-27T10:00:00"
            },
            ...
        }
    """
    checksums = {}
    data_dir = Path(data_dir).resolve()

    if not data_dir.exists():
        return checksums

    for file_path in data_dir.rglob("*"):
        if file_path.is_file():
            # Skip the checksum file itself
            if file_path.name == CHECKSUM_FILE_NAME:
                continue

            try:
                rel_path = str(file_path.relative_to(data_dir))
                sha256_hash = compute_file_hash(file_path)
                stat_info = file_path.stat()

                checksums[rel_path] = {
                    "sha256": sha256_hash,
                    "size_bytes": stat_info.st_size,
                    "timestamp": datetime.fromtimestamp(stat_info.st_mtime).isoformat()
                }
            except Exception as e:
                # Log error but continue processing other files
                print(f"Warning: Could not compute checksum for {file_path}: {e}")

    return checksums


def save_checksums(checksums: Dict[str, Dict[str, Any]], data_dir: Path) -> Path:
    """
    Save checksums to a JSON file in the specified data directory.

    Args:
        checksums: Dictionary of checksums to save.
        data_dir: Path to the data directory.

    Returns:
        Path to the saved checksum file.
    """
    checksum_file = _get_checksum_file_path(data_dir)
    ensure_dir(checksum_file.parent)

    metadata = {
        "generated_at": datetime.now().isoformat(),
        "data_dir": str(data_dir.resolve()),
        "file_count": len(checksums),
        "checksums": checksums
    }

    with open(checksum_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return checksum_file


def load_checksums(data_dir: Path) -> Optional[Dict[str, Dict[str, Any]]]:
    """
    Load checksums from the JSON file in the specified data directory.

    Args:
        data_dir: Path to the data directory.

    Returns:
        Dictionary of checksums or None if file doesn't exist.
    """
    checksum_file = _get_checksum_file_path(data_dir)

    if not checksum_file.exists():
        return None

    with open(checksum_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data.get("checksums")


def verify_checksums(data_dir: Path) -> Dict[str, bool]:
    """
    Verify current file checksums against stored values.

    Args:
        data_dir: Path to the data directory.

    Returns:
        Dictionary mapping file paths to verification status (True = valid).
    """
    stored_checksums = load_checksums(data_dir)

    if stored_checksums is None:
        return {}

    current_checksums = compute_directory_checksums(data_dir)
    results = {}

    for rel_path, stored_info in stored_checksums.items():
        if rel_path not in current_checksums:
            results[rel_path] = False  # File missing
            continue

        current_hash = current_checksums[rel_path]["sha256"]
        stored_hash = stored_info["sha256"]

        results[rel_path] = (current_hash == stored_hash)

    return results


def generate_checksums_for_directories() -> Dict[str, Path]:
    """
    Generate and save checksums for all configured data directories.

    Returns:
        Dictionary mapping directory names to their checksum file paths.
    """
    config = get_config()
    results = {}

    # Process raw data directory
    raw_dir = config.data_raw_path
    if raw_dir.exists():
        checksums = compute_directory_checksums(raw_dir)
        checksum_file = save_checksums(checksums, raw_dir)
        results["raw"] = checksum_file
        print(f"Generated checksums for {raw_dir}: {len(checksums)} files")
    else:
        print(f"Warning: Raw data directory does not exist: {raw_dir}")

    # Process processed data directory
    processed_dir = config.data_processed_path
    if processed_dir.exists():
        checksums = compute_directory_checksums(processed_dir)
        checksum_file = save_checksums(checksums, processed_dir)
        results["processed"] = checksum_file
        print(f"Generated checksums for {processed_dir}: {len(checksums)} files")
    else:
        print(f"Warning: Processed data directory does not exist: {processed_dir}")

    return results


def verify_all_checksums() -> bool:
    """
    Verify checksums for all data directories and return overall status.

    Returns:
        True if all checksums verify successfully, False otherwise.
    """
    config = get_config()
    all_valid = True

    for dir_name, dir_path in [("raw", config.data_raw_path), ("processed", config.data_processed_path)]:
        if not dir_path.exists():
            print(f"Skipping verification for {dir_name}: directory does not exist")
            continue

        results = verify_checksums(dir_path)
        if not results:
            print(f"No checksums found for {dir_name}")
            continue

        invalid_files = [f for f, valid in results.items() if not valid]
        if invalid_files:
            print(f"Verification FAILED for {dir_name}: {len(invalid_files)} files invalid")
            for f in invalid_files[:5]:  # Show first 5
                print(f"  - {f}")
            all_valid = False
        else:
            print(f"Verification PASSED for {dir_name}: {len(results)} files valid")

    return all_valid


def main():
    """Main entry point for checksum generation and verification."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Manage checksums for data directories"
    )
    parser.add_argument(
        "--generate",
        action="store_true",
        help="Generate and save checksums for all data directories"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify checksums for all data directories"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate and verify checksums"
    )

    args = parser.parse_args()

    if not any([args.generate, args.verify, args.all]):
        # Default to generate if no action specified
        args.generate = True

    if args.generate or args.all:
        print("=== Generating Checksums ===")
        results = generate_checksums_for_directories()
        for dir_name, file_path in results.items():
            print(f"  {dir_name}: {file_path}")

    if args.verify or args.all:
        print("\n=== Verifying Checksums ===")
        success = verify_all_checksums()
        if not success:
            print("\nWarning: Some checksums failed verification!")
            return 1

    print("\nDone.")
    return 0


if __name__ == "__main__":
    exit(main())
