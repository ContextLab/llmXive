"""
Checksums module for data integrity verification.

This module provides functions to compute and verify SHA-256 checksums
for files within the project's data directories. It is used to ensure
that downloaded and processed data files have not been corrupted or
modified unexpectedly.
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def compute_sha256(file_path: Path, chunk_size: int = 8192) -> str:
    """
    Compute the SHA-256 checksum of a file.

    Args:
        file_path: Path to the file to checksum.
        chunk_size: Size of chunks to read at a time (default 8KB).

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        PermissionError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def generate_checksums(
    data_dir: Path,
    file_patterns: Optional[List[str]] = None,
    output_path: Optional[Path] = None
) -> Dict[str, str]:
    """
    Generate checksums for all files in a directory (optionally filtered).

    Args:
        data_dir: Root directory to scan for files.
        file_patterns: Optional list of glob patterns to filter files.
                       If None, all files are included.
        output_path: Optional path to save the checksums as JSON.

    Returns:
        Dictionary mapping relative file paths to their SHA-256 checksums.
    """
    checksums = {}

    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    if file_patterns is None:
        file_patterns = ["**/*"]

    for pattern in file_patterns:
        for file_path in data_dir.glob(pattern):
            if file_path.is_file():
                rel_path = file_path.relative_to(data_dir)
                try:
                    checksum = compute_sha256(file_path)
                    checksums[str(rel_path)] = checksum
                except (PermissionError, OSError) as e:
                    # Log warning but continue with other files
                    print(f"Warning: Could not read {file_path}: {e}")

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(checksums, f, indent=2)

    return checksums


def verify_checksums(
    data_dir: Path,
    checksums: Dict[str, str],
    strict: bool = False
) -> Tuple[bool, List[str]]:
    """
    Verify files against a dictionary of expected checksums.

    Args:
        data_dir: Root directory where files are located.
        checksums: Dictionary mapping relative file paths to expected checksums.
        strict: If True, return False if any file is missing or mismatched.
                If False, only return the list of errors.

    Returns:
        Tuple of (all_passed, list_of_error_messages).
    """
    errors = []

    for rel_path, expected_checksum in checksums.items():
        file_path = data_dir / rel_path

        if not file_path.exists():
            errors.append(f"Missing file: {rel_path}")
            continue

        try:
            actual_checksum = compute_sha256(file_path)
            if actual_checksum != expected_checksum:
                errors.append(
                    f"Checksum mismatch: {rel_path}\n"
                    f"  Expected: {expected_checksum}\n"
                    f"  Actual:   {actual_checksum}"
                )
        except (PermissionError, OSError) as e:
            errors.append(f"Error reading {rel_path}: {e}")

    all_passed = len(errors) == 0
    return all_passed, errors


def main():
    """
    Command-line entry point for checksum operations.

    Usage:
        python code/utils/checksums.py generate <data_dir> [output_file]
        python code/utils/checksums.py verify <data_dir> <checksum_file>
    """
    import sys

    if len(sys.argv) < 3:
        print("Usage:")
        print("  generate <data_dir> [output_file]")
        print("  verify <data_dir> <checksum_file>")
        sys.exit(1)

    command = sys.argv[1]
    data_dir = Path(sys.argv[2])

    if command == "generate":
        output_file = Path(sys.argv[3]) if len(sys.argv) > 3 else data_dir / "checksums.json"
        checksums = generate_checksums(data_dir, output_path=output_file)
        print(f"Generated checksums for {len(checksums)} files.")
        print(f"Saved to: {output_file}")

    elif command == "verify":
        checksum_file = Path(sys.argv[3])
        if not checksum_file.exists():
            print(f"Error: Checksum file not found: {checksum_file}")
            sys.exit(1)

        with open(checksum_file, "r", encoding="utf-8") as f:
            checksums = json.load(f)

        passed, errors = verify_checksums(data_dir, checksums)
        if passed:
            print("All checksums verified successfully.")
        else:
            print(f"Verification failed with {len(errors)} errors:")
            for error in errors:
                print(f"  - {error}")
            sys.exit(1)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()