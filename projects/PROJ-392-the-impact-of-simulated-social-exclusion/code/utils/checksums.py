"""
Checksum utilities for data integrity verification.

This module provides functions to generate and verify MD5/SHA256 checksums
for files in the project's data directories. It is used to ensure that
downloaded and processed data files have not been corrupted or altered.
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Optional, Tuple


def compute_file_checksum(
    file_path: str | Path, algorithm: str = "sha256", chunk_size: int = 8192
) -> str:
    """
    Compute the checksum of a file using the specified algorithm.

    Args:
        file_path: Path to the file to checksum.
        algorithm: Hash algorithm to use ('md5', 'sha256', 'sha512').
        chunk_size: Size of chunks to read at a time.

    Returns:
        Hexadecimal string of the file's checksum.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If an unsupported algorithm is specified.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hash_obj = hashlib.new(algorithm)

    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            hash_obj.update(chunk)

    return hash_obj.hexdigest()


def generate_checksum_manifest(
    data_dir: str | Path,
    output_path: str | Path | None = None,
    algorithm: str = "sha256",
    extensions: list[str] | None = None,
) -> Dict[str, str]:
    """
    Generate a manifest of checksums for all files in a directory.

    Args:
        data_dir: Root directory to scan for files.
        output_path: Optional path to write the manifest as JSON.
        algorithm: Hash algorithm to use.
        extensions: Optional list of file extensions to include (e.g., ['.nii.gz', '.tsv']).
                   If None, all files are included.

    Returns:
        Dictionary mapping relative file paths to their checksums.
    """
    data_dir = Path(data_dir)
    if not data_dir.exists():
        raise FileNotFoundError(f"Directory not found: {data_dir}")

    manifest = {}

    for file_path in data_dir.rglob("*"):
        if file_path.is_file():
            if extensions:
                if file_path.suffix not in extensions:
                    continue

            rel_path = str(file_path.relative_to(data_dir))
            checksum = compute_file_checksum(file_path, algorithm)
            manifest[rel_path] = checksum

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

    return manifest


def verify_checksums(
    data_dir: str | Path,
    manifest_path: str | Path,
    algorithm: str = "sha256",
) -> Tuple[bool, Dict[str, str]]:
    """
    Verify file checksums against a stored manifest.

    Args:
        data_dir: Root directory where files are located.
        manifest_path: Path to the JSON manifest file.
        algorithm: Hash algorithm used in the manifest.

    Returns:
        Tuple of (all_valid: bool, failed_files: Dict[rel_path, reason]).
        failed_files maps relative paths to error messages (e.g., "mismatch", "missing").
    """
    data_dir = Path(data_dir)
    manifest_path = Path(manifest_path)

    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    failed_files = {}

    for rel_path, expected_checksum in manifest.items():
        file_path = data_dir / rel_path

        if not file_path.exists():
            failed_files[rel_path] = "missing"
            continue

        try:
            actual_checksum = compute_file_checksum(file_path, algorithm)
            if actual_checksum != expected_checksum:
                failed_files[rel_path] = "mismatch"
        except Exception as e:
            failed_files[rel_path] = f"error: {str(e)}"

    return len(failed_files) == 0, failed_files


def verify_single_file(
    file_path: str | Path, expected_checksum: str, algorithm: str = "sha256"
) -> bool:
    """
    Verify a single file's checksum against an expected value.

    Args:
        file_path: Path to the file.
        expected_checksum: Expected hexadecimal checksum string.
        algorithm: Hash algorithm to use.

    Returns:
        True if checksums match, False otherwise.
    """
    actual_checksum = compute_file_checksum(file_path, algorithm)
    return actual_checksum.lower() == expected_checksum.lower()
