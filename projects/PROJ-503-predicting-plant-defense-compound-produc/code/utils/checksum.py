"""
SHA-256 Checksum Validation Utility for Data Integrity (SC-004).

This module provides utilities to calculate, load, and validate SHA-256 checksums
for downloaded data files to ensure integrity.
"""

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Dict, Optional

# Configure logger
logger = logging.getLogger(__name__)


def calculate_sha256(file_path: str) -> str:
    """
    Calculate the SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        The hexadecimal SHA-256 hash string.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    sha256_hash = hashlib.sha256()
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        with open(path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise


def load_checksums(manifest_path: str) -> Dict[str, str]:
    """
    Load checksums from a JSON manifest file.

    Args:
        manifest_path: Path to the JSON manifest containing {filename: hash}.

    Returns:
        Dictionary mapping filenames to their expected SHA-256 hashes.

    Raises:
        FileNotFoundError: If the manifest does not exist.
        json.JSONDecodeError: If the manifest is not valid JSON.
    """
    path = Path(manifest_path)
    if not path.exists():
        raise FileNotFoundError(f"Checksum manifest not found: {manifest_path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_checksums(checksums: Dict[str, str], manifest_path: str) -> None:
    """
    Save a dictionary of checksums to a JSON manifest file.

    Args:
        checksums: Dictionary mapping filenames to SHA-256 hashes.
        manifest_path: Path where the JSON manifest will be written.
    """
    path = Path(manifest_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2)


def validate_checksum(file_path: str, expected_hash: str) -> bool:
    """
    Validate the SHA-256 checksum of a file against an expected hash.

    This is the primary utility function required by T022.

    Args:
        file_path: Path to the file to validate.
        expected_hash: The expected SHA-256 hexadecimal hash string.

    Returns:
        True if the calculated hash matches the expected hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the calculated hash does not match the expected hash.
    """
    calculated_hash = calculate_sha256(file_path)
    
    # Normalize hashes to lowercase for comparison
    calculated_hash = calculated_hash.lower()
    expected_hash = expected_hash.lower()

    if calculated_hash != expected_hash:
        raise ValueError(
            f"Checksum mismatch for {file_path}. "
            f"Expected: {expected_hash}, Got: {calculated_hash}"
        )
    
    logger.info(f"Checksum validation passed for {file_path}")
    return True


def validate_checksums_from_manifest(manifest_path: str, base_dir: Optional[str] = None) -> Dict[str, bool]:
    """
    Validate a set of files against a checksum manifest.

    Args:
        manifest_path: Path to the JSON manifest.
        base_dir: Optional base directory to prepend to filenames in the manifest.

    Returns:
        Dictionary mapping filenames to validation status (True/False).
    """
    checksums = load_checksums(manifest_path)
    results = {}

    for filename, expected_hash in checksums.items():
        full_path = Path(base_dir) / filename if base_dir else Path(filename)
        try:
            validate_checksum(str(full_path), expected_hash)
            results[filename] = True
        except Exception as e:
            logger.error(f"Validation failed for {filename}: {e}")
            results[filename] = False

    return results


def generate_checksums(file_paths: list, output_manifest: str) -> Dict[str, str]:
    """
    Generate SHA-256 checksums for a list of files and save to a manifest.

    Args:
        file_paths: List of file paths to hash.
        output_manifest: Path where the manifest JSON will be saved.

    Returns:
        Dictionary of {filename: hash}.
    """
    checksums = {}
    for file_path in file_paths:
        path = Path(file_path)
        if path.exists():
            checksums[path.name] = calculate_sha256(file_path)
        else:
            logger.warning(f"Skipping non-existent file: {file_path}")
    
    save_checksums(checksums, output_manifest)
    return checksums
