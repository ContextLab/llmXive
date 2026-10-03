"""
Data Integrity Checksums Module.

This module provides functions to compute, store, and verify cryptographic
checksums for data files to ensure integrity throughout the research pipeline.
"""

import os
import hashlib
import json
from pathlib import Path
from typing import Optional, Tuple

from utils.helpers import get_project_root, get_submissions_csv_path, ensure_data_dirs


class FileChecksumError(Exception):
    """Raised when a checksum verification fails."""
    pass


def compute_sha256(file_path: str) -> str:
    """
    Compute the SHA-256 checksum of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found for checksum: {file_path}")

    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Failed to read file for checksum: {file_path}") from e


def get_checksum_store_path() -> Path:
    """
    Get the path to the checksums store file.

    Returns:
        Path to the .checksums.json file in data/raw/.
    """
    project_root = get_project_root()
    return project_root / "data" / "raw" / ".checksums.json"


def load_checksums() -> dict:
    """
    Load existing checksums from the store file.

    Returns:
        Dictionary mapping file paths to their checksums.
    """
    store_path = get_checksum_store_path()
    if not store_path.exists():
        return {}

    try:
        with open(store_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        # If the file is corrupted or unreadable, start fresh
        return {}


def store_data_checksum(file_path: str, checksum: Optional[str] = None) -> None:
    """
    Store a checksum for a file in the persistent store.

    Args:
        file_path: Path to the file.
        checksum: Optional pre-computed checksum. If None, computes it.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if checksum is None:
        checksum = compute_sha256(file_path)

    store_path = get_checksum_store_path()
    ensure_data_dirs()  # Ensure data/raw exists

    # Load existing checksums
    checksums = load_checksums()

    # Update with new checksum
    checksums[file_path] = checksum

    # Write back atomically (write to temp, then rename)
    temp_path = str(store_path) + ".tmp"
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(checksums, f, indent=2)
        os.replace(temp_path, str(store_path))
    except Exception as e:
        # Clean up temp file if it exists
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise IOError(f"Failed to store checksum: {e}") from e


def verify_data_checksum(file_path: str, expected_checksum: Optional[str] = None) -> bool:
    """
    Verify the checksum of a file against a stored value.

    Args:
        file_path: Path to the file to verify.
        expected_checksum: Optional expected checksum. If None, loads from store.

    Returns:
        True if checksums match.

    Raises:
        FileChecksumError: If checksums do not match or no checksum is stored.
        FileNotFoundError: If the file does not exist.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found for verification: {file_path}")

    current_checksum = compute_sha256(file_path)

    if expected_checksum is None:
        checksums = load_checksums()
        expected_checksum = checksums.get(file_path)

    if expected_checksum is None:
        raise FileChecksumError(
            f"No stored checksum found for file: {file_path}. "
            "Run store_data_checksum first."
        )

    if current_checksum != expected_checksum:
        raise FileChecksumError(
            f"Checksum mismatch for file: {file_path}\n"
            f"  Expected: {expected_checksum}\n"
            f"  Current:  {current_checksum}"
        )

    return True


def verify_submissions_integrity() -> bool:
    """
    Verify the integrity of the submissions CSV file.

    This is a convenience function specifically for the main data file.

    Returns:
        True if verification passes.

    Raises:
        FileChecksumError: If verification fails.
        FileNotFoundError: If the file does not exist.
    """
    submissions_path = get_submissions_csv_path()
    return verify_data_checksum(str(submissions_path))


def main():
    """
    Command-line interface for checksum operations.

    Usage:
        python -m utils.checksums compute <file_path>
        python -m utils.checksums store <file_path>
        python -m utils.checksums verify <file_path>
    """
    import sys

    if len(sys.argv) < 3:
        print("Usage: python -m utils.checksums <command> <file_path>")
        print("Commands: compute, store, verify")
        sys.exit(1)

    command = sys.argv[1]
    file_path = sys.argv[2]

    try:
        if command == "compute":
            checksum = compute_sha256(file_path)
            print(f"SHA-256: {checksum}")

        elif command == "store":
            store_data_checksum(file_path)
            print(f"Checksum stored for: {file_path}")

        elif command == "verify":
            verify_submissions_integrity() if file_path == "submissions" else verify_data_checksum(file_path)
            print(f"Checksum verified for: {file_path}")

        else:
            print(f"Unknown command: {command}")
            sys.exit(1)

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except FileChecksumError as e:
        print(f"Integrity Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()