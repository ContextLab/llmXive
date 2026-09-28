"""
Data Integrity Checksums Module.

Provides functionality to compute, store, and verify SHA-256 checksums for data files
to ensure data integrity throughout the research pipeline.
"""

import os
import hashlib
import json
from pathlib import Path
from typing import Optional, Tuple

# Import existing helpers from utils.helpers
# These are defined in the existing API surface provided in the prompt
from utils.helpers import get_project_root, get_submissions_csv_path, ensure_data_dirs


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
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for checksum: {file_path}")

    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Error reading file {file_path}: {e}")


def get_checksum_store_path() -> Path:
    """
    Get the path where checksums are stored.

    Returns:
        Path to the checksums JSON file.
    """
    project_root = get_project_root()
    return project_root / "data" / "processed" / "checksums.json"


def store_data_checksum(file_path: str, checksum: Optional[str] = None) -> None:
    """
    Store the checksum of a file in the checksums store.

    Args:
        file_path: Path to the file.
        checksum: Optional pre-computed checksum. If None, it will be computed.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the checksum store cannot be written.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Cannot store checksum: file not found {file_path}")

    if checksum is None:
        checksum = compute_sha256(file_path)

    store_path = get_checksum_store_path()
    ensure_data_dirs()  # Ensure data/processed exists

    # Load existing checksums or initialize
    checksums = {}
    if store_path.exists():
        try:
            with open(store_path, "r", encoding="utf-8") as f:
                checksums = json.load(f)
        except (json.JSONDecodeError, IOError):
            checksums = {}

    # Store the new checksum keyed by the relative file path
    relative_path = str(file_path.relative_to(get_project_root()))
    checksums[relative_path] = {
        "checksum": checksum,
        "timestamp": os.path.getmtime(file_path)
    }

    # Write back atomically (write to temp, then rename)
    temp_path = store_path.with_suffix(".tmp")
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(checksums, f, indent=2)
        os.replace(temp_path, store_path)
    except IOError as e:
        if temp_path.exists():
            temp_path.unlink()
        raise IOError(f"Failed to write checksum store: {e}")


def verify_data_checksum(file_path: str) -> Tuple[bool, str, str]:
    """
    Verify the checksum of a file against the stored checksum.

    Args:
        file_path: Path to the file to verify.

    Returns:
        Tuple of (is_valid, current_checksum, stored_checksum).
        If no stored checksum exists, stored_checksum is None.

    Raises:
        FileNotFoundError: If the file or checksum store does not exist.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for verification: {file_path}")

    current_checksum = compute_sha256(file_path)

    store_path = get_checksum_store_path()
    if not store_path.exists():
        return False, current_checksum, None

    try:
        with open(store_path, "r", encoding="utf-8") as f:
            checksums = json.load(f)
    except (json.JSONDecodeError, IOError):
        return False, current_checksum, None

    relative_path = str(file_path.relative_to(get_project_root()))
    if relative_path not in checksums:
        return False, current_checksum, None

    stored_checksum = checksums[relative_path]["checksum"]
    return current_checksum == stored_checksum, current_checksum, stored_checksum


def verify_submissions_integrity() -> bool:
    """
    Verify the integrity of the submissions CSV file.

    This function computes the current SHA-256 checksum of data/raw/submissions.csv
    and compares it against the stored checksum.

    Returns:
        True if the checksum matches or if no stored checksum exists (first run).

    Raises:
        FileNotFoundError: If the submissions file does not exist.
        ValueError: If the checksum mismatches (data integrity failure).
    """
    submissions_path = get_submissions_csv_path()

    if not Path(submissions_path).exists():
        raise FileNotFoundError(f"Submissions file not found: {submissions_path}")

    # Check if we have a stored checksum to verify against
    is_valid, current, stored = verify_data_checksum(submissions_path)

    if stored is None:
        # First time running or no stored checksum.
        # We store the current checksum for future verification.
        store_data_checksum(submissions_path, current)
        return True

    if not is_valid:
        raise ValueError(
            f"DATA INTEGRITY FAILURE: Checksum mismatch for {submissions_path}.\n"
            f"  Expected: {stored}\n"
            f"  Found:    {current}\n"
            "The data file has been modified or corrupted since the last checksum was recorded."
        )

    return True


def main() -> None:
    """
    CLI entry point for checksum operations.

    Usage:
        python code/utils/checksums.py --store  : Compute and store checksum for submissions.csv
        python code/utils/checksums.py --verify : Verify checksum of submissions.csv
    """
    import argparse

    parser = argparse.ArgumentParser(description="Data Integrity Checksums Utility")
    parser.add_argument(
        "--store",
        action="store_true",
        help="Compute and store the SHA-256 checksum for data/raw/submissions.csv"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify the SHA-256 checksum of data/raw/submissions.csv against stored value"
    )

    args = parser.parse_args()

    if not args.store and not args.verify:
        parser.print_help()
        print("\nPlease specify --store or --verify.")
        return

    try:
        if args.store:
            print(f"Storing checksum for {get_submissions_csv_path()}...")
            store_data_checksum(get_submissions_csv_path())
            print("Checksum stored successfully.")

        if args.verify:
            print(f"Verifying checksum for {get_submissions_csv_path()}...")
            if verify_submissions_integrity():
                print("Integrity check passed.")
            else:
                # This path should technically not be reached if verify_submissions_integrity raises on mismatch
                # But kept for safety if logic changes
                print("Integrity check failed or no stored checksum.")

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return
    except ValueError as e:
        print(f"CRITICAL ERROR: {e}")
        return
    except Exception as e:
        print(f"Unexpected error: {e}")
        return


if __name__ == "__main__":
    main()
