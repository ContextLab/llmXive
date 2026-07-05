"""
Checksum utility for raw data integrity.

Provides functions to compute SHA-256 checksums for individual files and
directories, save/load checksum manifests, and verify data integrity
against stored manifests.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Optional, Tuple, List

from logging_config import get_logger, info, error, warning

logger = get_logger(__name__)

# Constants
CHECKSUM_MANIFEST_NAME = "checksums.json"
CHUNK_SIZE = 8192  # 8KB chunks for reading large files


def compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        error(f"Error reading file {file_path}: {e}")
        raise


def generate_checksum_for_file(file_path: Path) -> Tuple[Path, str]:
    """
    Wrapper for compute_sha256 returning a tuple of (path, hash).

    Args:
        file_path: Path to the file.

    Returns:
        Tuple of (Path, hex_digest).
    """
    info(f"Generating checksum for: {file_path}")
    checksum = compute_sha256(file_path)
    return file_path, checksum


def compute_checksums_for_directory(
    directory_path: Path,
    recursive: bool = True,
    extensions: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Compute checksums for all files in a directory.

    Args:
        directory_path: Path to the directory.
        recursive: If True, traverse subdirectories.
        extensions: Optional list of file extensions to include (e.g., ['.csv', '.json']).
                   If None, all files are included.

    Returns:
        Dictionary mapping relative file paths (string) to their SHA-256 hashes.
    """
    if not directory_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory_path}")

    checksums = {}
    walker = directory_path.rglob('*') if recursive else directory_path.glob('*')

    count = 0
    for file_path in walker:
        if file_path.is_file():
            # Filter by extension if provided
            if extensions:
                if file_path.suffix.lower() not in [ext.lower() for ext in extensions]:
                    continue

            try:
                rel_path = file_path.relative_to(directory_path)
                checksum = compute_sha256(file_path)
                checksums[str(rel_path)] = checksum
                count += 1
                if count % 100 == 0:
                    debug(f"Processed {count} files...")
            except Exception as e:
                warning(f"Skipping file {file_path} due to error: {e}")

    info(f"Computed checksums for {count} files in {directory_path}")
    return checksums


def save_checksums(checksums: Dict[str, str], output_path: Path) -> None:
    """
    Save checksums to a JSON manifest file.

    Args:
        checksums: Dictionary mapping relative paths to hashes.
        output_path: Path where the manifest will be saved.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(checksums, f, indent=2)
        info(f"Saved checksums to {output_path}")
    except IOError as e:
        error(f"Failed to save checksums to {output_path}: {e}")
        raise


def load_checksums(manifest_path: Path) -> Dict[str, str]:
    """
    Load checksums from a JSON manifest file.

    Args:
        manifest_path: Path to the manifest file.

    Returns:
        Dictionary mapping relative paths to hashes.

    Raises:
        FileNotFoundError: If manifest does not exist.
        json.JSONDecodeError: If manifest is invalid JSON.
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"Checksum manifest not found: {manifest_path}")

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        error(f"Invalid JSON in checksum manifest {manifest_path}: {e}")
        raise


def verify_checksums(
    directory_path: Path,
    manifest_path: Optional[Path] = None
) -> Tuple[bool, Dict[str, str], Dict[str, str]]:
    """
    Verify files in a directory against a checksum manifest.

    If manifest_path is not provided, it looks for 'checksums.json' in the directory.

    Args:
        directory_path: Root directory containing the data files.
        manifest_path: Optional path to the checksum manifest.

    Returns:
        Tuple of:
            - bool: True if all files match, False otherwise.
            - Dict[str, str]: Expected checksums from manifest.
            - Dict[str, str]: Actual computed checksums.

    Raises:
        FileNotFoundError: If manifest is missing.
    """
    if manifest_path is None:
        manifest_path = directory_path / CHECKSUM_MANIFEST_NAME

    expected = load_checksums(manifest_path)
    actual = compute_checksums_for_directory(directory_path)

    all_match = True
    mismatches = {}
    missing_files = []

    # Check for missing files in actual vs expected
    for rel_path in expected:
        if rel_path not in actual:
            missing_files.append(rel_path)
            all_match = False

    # Check for mismatches
    for rel_path, expected_hash in expected.items():
        if rel_path in actual:
            if actual[rel_path] != expected_hash:
                mismatches[rel_path] = {
                    "expected": expected_hash,
                    "actual": actual[rel_path]
                }
                all_match = False
                warning(f"Mismatch detected for {rel_path}")
        # else handled above

    if missing_files:
        error(f"Missing files in directory: {missing_files}")

    if all_match:
        info("Verification successful: All checksums match.")
    else:
        error("Verification failed: Checksums do not match.")

    return all_match, expected, actual


def main():
    """
    CLI entry point for checksum operations.

    Usage:
        python checksums.py generate <directory> [output]
        python checksums.py verify <directory> [manifest]

    Examples:
        python checksums.py generate data/raw
        python checksums.py verify data/raw
    """
    import sys

    if len(sys.argv) < 3:
        print("Usage: python checksums.py <generate|verify> <directory> [output_manifest]")
        sys.exit(1)

    command = sys.argv[1]
    directory = Path(sys.argv[2])
    output_manifest = None
    if len(sys.argv) > 3:
        output_manifest = Path(sys.argv[3])

    if not directory.exists():
        error(f"Directory not found: {directory}")
        sys.exit(1)

    if command == "generate":
        if output_manifest is None:
            output_manifest = directory / CHECKSUM_MANIFEST_NAME

        info(f"Generating checksums for {directory}...")
        checksums = compute_checksums_for_directory(directory)
        save_checksums(checksums, output_manifest)
        print(f"Checksums saved to {output_manifest}")

    elif command == "verify":
        if output_manifest is None:
            output_manifest = directory / CHECKSUM_MANIFEST_NAME

        info(f"Verifying checksums for {directory} using {output_manifest}...")
        try:
            success, expected, actual = verify_checksums(directory, output_manifest)
            if success:
                print("VERIFICATION PASSED: All files match.")
                sys.exit(0)
            else:
                print("VERIFICATION FAILED: Mismatches or missing files detected.")
                sys.exit(1)
        except Exception as e:
            error(f"Verification failed with error: {e}")
            sys.exit(1)
    else:
        error(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()