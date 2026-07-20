"""
Checksum utilities for file integrity verification.

Provides functions to calculate SHA-256 hashes for files and strings,
verify file checksums against known values, and manage checksum manifests.
"""
import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union

from src.logging_config import get_data_ingestion_logger

logger = get_data_ingestion_logger(__name__)


def compute_string_sha256(data: str) -> str:
    """
    Compute the SHA-256 hash of a string.

    Args:
        data: The string to hash.

    Returns:
        The hexadecimal SHA-256 hash string.
    """
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def compute_file_sha256(file_path: Union[str, Path], chunk_size: int = 8192) -> str:
    """
    Compute the SHA-256 hash of a file by reading it in chunks.

    This is memory-efficient for large files.

    Args:
        file_path: Path to the file to hash.
        chunk_size: Size of chunks to read (default 8KB).

    Returns:
        The hexadecimal SHA-256 hash string.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                sha256_hash.update(chunk)
    except IOError as e:
        logger.error(f"Failed to read file {file_path}: {e}")
        raise

    return sha256_hash.hexdigest()


def calculate_sha256(file_path: str) -> str:
    """
    Calculate the SHA-256 checksum of a file.

    This is a convenience wrapper around compute_file_sha256.

    Args:
        file_path: Path to the file to hash.

    Returns:
        The hexadecimal SHA-256 hash string.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    return compute_file_sha256(file_path)


def verify_file_checksum(file_path: Union[str, Path], expected_checksum: str) -> bool:
    """
    Verify a file's checksum against an expected value.

    Args:
        file_path: Path to the file to verify.
        expected_checksum: The expected SHA-256 hash string.

    Returns:
        True if the checksum matches, False otherwise.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    actual_checksum = compute_file_sha256(file_path)
    is_valid = actual_checksum.lower() == expected_checksum.lower()
    if not is_valid:
        logger.warning(
            f"Checksum mismatch for {file_path}. "
            f"Expected: {expected_checksum}, Got: {actual_checksum}"
        )
    return is_valid


def generate_checksum_manifest(file_paths: list, output_path: Union[str, Path]) -> None:
    """
    Generate a JSON manifest containing checksums for multiple files.

    Args:
        file_paths: List of file paths to include in the manifest.
        output_path: Path where the manifest JSON will be written.

    Raises:
        FileNotFoundError: If any file in file_paths does not exist.
        IOError: If the output file cannot be written.
    """
    manifest = {
        "version": "1.0",
        "algorithm": "sha256",
        "files": {}
    }

    for file_path in file_paths:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found in manifest generation: {path}")
        manifest["files"][str(path)] = compute_file_sha256(path)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"Checksum manifest written to {output_path}")
    except IOError as e:
        logger.error(f"Failed to write manifest to {output_path}: {e}")
        raise


def load_checksum_manifest(manifest_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a checksum manifest from a JSON file.

    Args:
        manifest_path: Path to the manifest JSON file.

    Returns:
        The manifest dictionary.

    Raises:
        FileNotFoundError: If the manifest file does not exist.
        json.JSONDecodeError: If the manifest is not valid JSON.
    """
    manifest_path = Path(manifest_path)
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")

    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in manifest {manifest_path}: {e}")
        raise


def verify_manifest(manifest_path: Union[str, Path]) -> Dict[str, bool]:
    """
    Verify all files listed in a checksum manifest.

    Args:
        manifest_path: Path to the manifest JSON file.

    Returns:
        A dictionary mapping file paths to their verification status (True/False).

    Raises:
        FileNotFoundError: If the manifest file does not exist.
    """
    manifest = load_checksum_manifest(manifest_path)
    results = {}

    for file_path, expected_checksum in manifest.get("files", {}).items():
        try:
            results[file_path] = verify_file_checksum(file_path, expected_checksum)
        except FileNotFoundError:
            results[file_path] = False
            logger.error(f"File missing during manifest verification: {file_path}")

    return results