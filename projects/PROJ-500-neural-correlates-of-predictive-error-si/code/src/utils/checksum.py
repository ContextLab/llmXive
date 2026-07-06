"""
Checksum utilities for data hygiene (FR-009, Constitution III).

Provides functions to compute and verify SHA-256 checksums for data artifacts
to ensure data integrity throughout the pipeline.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Optional, List


def compute_file_sha256(file_path: str, chunk_size: int = 8192) -> str:
    """
    Compute the SHA-256 checksum of a file.

    Reads the file in chunks to handle large files without excessive memory usage.

    Args:
        file_path: Path to the file to hash.
        chunk_size: Size of chunks to read (default 8KB).

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    sha256_hash = hashlib.sha256()
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not path.is_file():
        raise IOError(f"Path is not a file: {file_path}")

    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256_hash.update(chunk)

    return sha256_hash.hexdigest()


def compute_directory_checksums(
    directory_path: str, extensions: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Compute checksums for all files in a directory.

    Args:
        directory_path: Path to the directory to scan.
        extensions: Optional list of file extensions to include (e.g., ['.csv', '.json']).
                   If None, all files are included.

    Returns:
        Dictionary mapping relative file paths to their SHA-256 checksums.
    """
    checksums = {}
    base_path = Path(directory_path)

    if not base_path.exists() or not base_path.is_dir():
        raise NotADirectoryError(f"Directory not found: {directory_path}")

    for file_path in base_path.rglob("*"):
        if file_path.is_file():
            if extensions is None or file_path.suffix.lower() in extensions:
                rel_path = str(file_path.relative_to(base_path))
                checksums[rel_path] = compute_file_sha256(str(file_path))

    return checksums


def save_checksum_manifest(
    checksums: Dict[str, str], output_path: str
) -> None:
    """
    Save checksums to a JSON manifest file.

    Args:
        checksums: Dictionary of file paths to checksums.
        output_path: Path where the manifest JSON file will be written.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    manifest = {
        "version": "1.0",
        "algorithm": "sha256",
        "checksums": checksums
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def load_checksum_manifest(manifest_path: str) -> Dict[str, str]:
    """
    Load checksums from a JSON manifest file.

    Args:
        manifest_path: Path to the manifest JSON file.

    Returns:
        Dictionary of file paths to checksums.

    Raises:
        FileNotFoundError: If the manifest file does not exist.
        ValueError: If the manifest format is invalid.
    """
    path = Path(manifest_path)

    if not path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "checksums" not in data:
        raise ValueError("Invalid manifest format: missing 'checksums' key")

    return data["checksums"]


def verify_checksums(
    directory_path: str, manifest_path: str
) -> Dict[str, bool]:
    """
    Verify current file checksums against a manifest.

    Args:
        directory_path: Base directory where files are located.
        manifest_path: Path to the checksum manifest JSON file.

    Returns:
        Dictionary mapping relative file paths to verification status (True/False).
    """
    manifest_checksums = load_checksum_manifest(manifest_path)
    results = {}
    base_path = Path(directory_path)

    for rel_path, expected_hash in manifest_checksums.items():
        full_path = base_path / rel_path

        if not full_path.exists():
            results[rel_path] = False
            continue

        try:
            actual_hash = compute_file_sha256(str(full_path))
            results[rel_path] = (actual_hash == expected_hash)
        except Exception:
            results[rel_path] = False

    return results


def generate_and_save_manifest(
    directory_path: str, output_path: str, extensions: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Compute checksums for a directory and save them to a manifest.

    Args:
        directory_path: Base directory to scan.
        output_path: Path where the manifest will be saved.
        extensions: Optional list of file extensions to include.

    Returns:
        Dictionary of computed checksums.
    """
    checksums = compute_directory_checksums(directory_path, extensions)
    save_checksum_manifest(checksums, output_path)
    return checksums
