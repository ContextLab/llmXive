"""
Enhanced checksum utilities for the project.

This module provides comprehensive checksum functionality for data hygiene,
including file checksumming, directory checksums, and manifest management.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Union, Optional

from .config import get_project_paths


def compute_file_checksum(file_path: Union[str, Path], algorithm: str = 'sha256') -> str:
    """
    Compute checksum of a single file.

    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use (sha256, md5, sha1)

    Returns:
        Hexadecimal checksum string
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hash_func = hashlib.new(algorithm)

    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hash_func.update(chunk)

    return hash_func.hexdigest()


def compute_directory_checksums(
    directory: Union[str, Path],
    recursive: bool = True,
    algorithm: str = 'sha256',
    patterns: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Compute checksums for all files in a directory.

    Args:
        directory: Path to the directory
        recursive: Whether to search subdirectories
        algorithm: Hash algorithm to use
        patterns: Optional list of glob patterns to filter files

    Returns:
        Dictionary mapping relative file paths to checksums
    """
    directory = Path(directory)
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    checksums = {}

    if recursive:
        files = directory.rglob('*')
    else:
        files = directory.glob('*')

    for file_path in files:
        if file_path.is_file():
            # Apply pattern filters if provided
            if patterns:
                if not any(file_path.match(pattern) for pattern in patterns):
                    continue

            try:
                checksum = compute_file_checksum(file_path, algorithm)
                rel_path = str(file_path.relative_to(directory))
                checksums[rel_path] = checksum
            except Exception as e:
                # Log but continue with other files
                print(f"Warning: Could not checksum {file_path}: {e}")

    return checksums


def save_checksum_manifest(
    checksums: Dict[str, str],
    output_path: Union[str, Path],
    metadata: Optional[Dict] = None
) -> Path:
    """
    Save checksums to a JSON manifest file.

    Args:
        checksums: Dictionary of file paths to checksums
        output_path: Path for the output manifest file
        metadata: Optional metadata to include in the manifest

    Returns:
        Path to the created manifest file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    manifest = {
        "checksums": checksums,
        "algorithm": "sha256",
        "total_files": len(checksums),
        "metadata": metadata or {}
    }

    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    return output_path


def load_checksum_manifest(manifest_path: Union[str, Path]) -> Dict:
    """
    Load checksums from a JSON manifest file.

    Args:
        manifest_path: Path to the manifest file

    Returns:
        Dictionary containing checksums and metadata
    """
    manifest_path = Path(manifest_path)
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    with open(manifest_path, 'r') as f:
        return json.load(f)


def verify_checksums(
    base_directory: Union[str, Path],
    manifest_path: Union[str, Path],
    verbose: bool = False
) -> Dict[str, bool]:
    """
    Verify files against a checksum manifest.

    Args:
        base_directory: Base directory containing the files
        manifest_path: Path to the checksum manifest
        verbose: Whether to print verification details

    Returns:
        Dictionary mapping file paths to verification status (True/False)
    """
    base_directory = Path(base_directory)
    manifest = load_checksum_manifest(manifest_path)
    expected_checksums = manifest.get("checksums", {})

    results = {}

    for rel_path, expected_checksum in expected_checksums.items():
        file_path = base_directory / rel_path

        if not file_path.exists():
            results[rel_path] = False
            if verbose:
                print(f"MISSING: {rel_path}")
            continue

        try:
            actual_checksum = compute_file_checksum(file_path)
            is_valid = actual_checksum == expected_checksum
            results[rel_path] = is_valid

            if verbose:
                status = "✓" if is_valid else "✗"
                print(f"{status} {rel_path}")

        except Exception as e:
            results[rel_path] = False
            if verbose:
                print(f"ERROR: {rel_path} - {e}")

    return results


# Convenience functions for specific project directories
def checksum_raw_data():
    """Compute and save checksums for raw data directory."""
    paths = get_project_paths()
    raw_dir = paths["data_raw"]
    state_dir = paths["state"]

    checksums = compute_directory_checksums(raw_dir, patterns=["*.npy"])
    manifest_path = state_dir / "checksums_raw.json"
    save_checksum_manifest(checksums, manifest_path, {"source": "raw_data"})

    return manifest_path


def checksum_processed_data():
    """Compute and save checksums for processed data directory."""
    paths = get_project_paths()
    processed_dir = paths["data_processed"]
    state_dir = paths["state"]

    checksums = compute_directory_checksums(processed_dir)
    manifest_path = state_dir / "checksums_processed.json"
    save_checksum_manifest(checksums, manifest_path, {"source": "processed_data"})

    return manifest_path