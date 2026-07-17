"""
Checksum verification utility for data integrity.

Implements Constitution Principle III: Data Hygiene
- Computes SHA-256 checksums for all files in data directories
- Stores checksums in JSON files
- Verifies data integrity on demand
- Updates checksums when data changes
"""

import os
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import sys

# Constants
DATA_DIRS = [
    Path("data/raw"),
    Path("data/generated"),
    Path("data/results")
]

CHECKSUM_DIR = Path("data/checksums")
CHECKSUM_SUFFIX = "_checksums.json"


def compute_sha256(file_path: Path) -> str:
    """
    Compute SHA-256 hash of a file.

    Args:
        file_path: Path to the file

    Returns:
        Hexadecimal string of the SHA-256 hash
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def scan_directory(directory: Path) -> List[Path]:
    """
    Recursively scan directory for all files.

    Args:
        directory: Path to the directory to scan

    Returns:
        List of file paths
    """
    if not directory.exists():
        return []

    files = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            # Skip checksum files themselves
            if filename.endswith(CHECKSUM_SUFFIX):
                continue
            files.append(Path(root) / filename)
    return files


def load_existing_checksums(checksum_file: Path) -> Dict[str, str]:
    """
    Load existing checksums from JSON file.

    Args:
        checksum_file: Path to the checksum JSON file

    Returns:
        Dictionary mapping file paths to checksums
    """
    if not checksum_file.exists():
        return {}

    with open(checksum_file, "r") as f:
        return json.load(f)


def save_checksums(checksums: Dict[str, str], checksum_file: Path) -> None:
    """
    Save checksums to JSON file.

    Args:
        checksums: Dictionary mapping file paths to checksums
        checksum_file: Path to save the checksum JSON file
    """
    checksum_file.parent.mkdir(parents=True, exist_ok=True)
    with open(checksum_file, "w") as f:
        json.dump(checksums, f, indent=2)


def verify_data_integrity(directory: Path, verbose: bool = True) -> Tuple[bool, List[str]]:
    """
    Verify integrity of all files in a directory against stored checksums.

    Args:
        directory: Directory to verify
        verbose: Whether to print verification results

    Returns:
        Tuple of (all_valid, list_of_invalid_files)
    """
    checksum_file = directory.parent / f"{directory.name}{CHECKSUM_SUFFIX}"
    stored_checksums = load_existing_checksums(checksum_file)

    if not stored_checksums:
        if verbose:
            print(f"No stored checksums found for {directory}. Run update first.")
        return False, []

    files = scan_directory(directory)
    all_valid = True
    invalid_files = []

    for file_path in files:
        relative_path = str(file_path)
        if relative_path not in stored_checksums:
            if verbose:
                print(f"Warning: No stored checksum for {file_path}")
            continue

        current_hash = compute_sha256(file_path)
        stored_hash = stored_checksums[relative_path]

        if current_hash != stored_hash:
            all_valid = False
            invalid_files.append(str(file_path))
            if verbose:
                print(f"INVALID: {file_path}")
                print(f"  Expected: {stored_hash}")
                print(f"  Got:      {current_hash}")
        elif verbose:
            print(f"OK: {file_path}")

    return all_valid, invalid_files


def update_checksums(directory: Path, verbose: bool = True) -> Dict[str, str]:
    """
    Compute and store checksums for all files in a directory.

    Args:
        directory: Directory to process
        verbose: Whether to print progress

    Returns:
        Dictionary of file paths to checksums
    """
    files = scan_directory(directory)
    checksums = {}

    for file_path in files:
        relative_path = str(file_path)
        checksum = compute_sha256(file_path)
        checksums[relative_path] = checksum

        if verbose:
            print(f"Computed: {file_path} -> {checksum[:16]}...")

    # Save checksums
    checksum_file = directory.parent / f"{directory.name}{CHECKSUM_SUFFIX}"
    save_checksums(checksums, checksum_file)

    if verbose:
        print(f"Saved {len(checksums)} checksums to {checksum_file}")

    return checksums


def main():
    """Main entry point for checksum verification."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Verify or update checksums for data directories"
    )
    parser.add_argument(
        "command",
        choices=["verify", "update", "verify-all", "update-all"],
        help="Command to execute"
    )
    parser.add_argument(
        "--directory",
        type=str,
        default=None,
        help="Specific directory to process (default: all data dirs)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress output"
    )

    args = parser.parse_args()
    verbose = not args.quiet

    # Determine directories to process
    if args.directory:
        directories = [Path(args.directory)]
    else:
        directories = DATA_DIRS

    if args.command == "verify":
        for directory in directories:
            print(f"\nVerifying: {directory}")
            valid, invalid = verify_data_integrity(directory, verbose)
            if not valid and invalid:
                print(f"Failed: {len(invalid)} files failed verification")
                sys.exit(1)

    elif args.command == "update":
        for directory in directories:
            print(f"\nUpdating: {directory}")
            update_checksums(directory, verbose)

    elif args.command == "verify-all":
        all_valid = True
        for directory in directories:
            print(f"\nVerifying: {directory}")
            valid, invalid = verify_data_integrity(directory, verbose)
            if not valid:
                all_valid = False
        if not all_valid:
            print("\nOverall: FAILED")
            sys.exit(1)
        else:
            print("\nOverall: PASSED")

    elif args.command == "update-all":
        for directory in directories:
            print(f"\nUpdating: {directory}")
            update_checksums(directory, verbose)
        print("\nAll checksums updated.")

if __name__ == "__main__":
    main()