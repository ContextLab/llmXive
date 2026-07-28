"""
Checksum utility module for managing SHA-256 hashes of data artifacts.

This module provides functionality to:
- Compute SHA-256 hashes for files
- Load and save a central checksum registry (data/checksums.json)
- Verify file integrity against stored checksums
- Update checksums for modified files
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List

# Define the checksum registry path relative to project root
CHECKSUM_REGISTRY_PATH = Path("data/checksums.json")

class ChecksumError(Exception):
    """Custom exception for checksum-related errors."""
    pass


def compute_file_sha256(file_path: Path) -> str:
    """
    Compute the SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        ChecksumError: If the file does not exist or cannot be read.
    """
    if not file_path.exists():
        raise ChecksumError(f"File not found: {file_path}")

    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise ChecksumError(f"Failed to read file {file_path}: {e}")


def load_checksums() -> Dict[str, Any]:
    """
    Load the checksum registry from data/checksums.json.

    Returns:
        Dictionary containing the checksum registry.
        Returns an empty registry structure if the file does not exist.
    """
    if not CHECKSUM_REGISTRY_PATH.exists():
        # Ensure the data directory exists
        CHECKSUM_REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
        return {"files": {}}

    try:
        with open(CHECKSUM_REGISTRY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ChecksumError(f"Invalid JSON in checksum registry: {e}")
    except IOError as e:
        raise ChecksumError(f"Failed to load checksum registry: {e}")


def save_checksums(data: Dict[str, Any]) -> None:
    """
    Save the checksum registry to data/checksums.json.

    Args:
        data: The checksum registry dictionary to save.

    Raises:
        ChecksumError: If the file cannot be written.
    """
    # Ensure the data directory exists
    CHECKSUM_REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(CHECKSUM_REGISTRY_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except IOError as e:
        raise ChecksumError(f"Failed to save checksum registry: {e}")


def update_checksum_for_file(file_path: Path) -> Dict[str, str]:
    """
    Compute the hash for a file and update the registry.

    Args:
        file_path: Path to the file to register.

    Returns:
        Dictionary with the file path and its new hash.

    Raises:
        ChecksumError: If file operations fail.
    """
    if not file_path.exists():
        raise ChecksumError(f"Cannot update checksum: file not found {file_path}")

    file_hash = compute_file_sha256(file_path)
    registry = load_checksums()

    # Store relative path from project root for portability
    try:
        relative_path = str(file_path.relative_to(Path.cwd()))
    except ValueError:
        # If not under current working directory, use absolute path
        relative_path = str(file_path)

    registry["files"][relative_path] = {
        "hash": file_hash,
        "algorithm": "sha256"
    }

    save_checksums(registry)
    return {"path": relative_path, "hash": file_hash}


def verify_file_integrity(file_path: Path) -> bool:
    """
    Verify a file's integrity against its stored checksum.

    Args:
        file_path: Path to the file to verify.

    Returns:
        True if the file matches the stored checksum.

    Raises:
        ChecksumError: If the file is not in the registry or verification fails.
    """
    try:
        relative_path = str(file_path.relative_to(Path.cwd()))
    except ValueError:
        relative_path = str(file_path)

    registry = load_checksums()

    if relative_path not in registry["files"]:
        raise ChecksumError(f"No stored checksum found for: {relative_path}")

    stored_entry = registry["files"][relative_path]
    if stored_entry.get("algorithm") != "sha256":
        raise ChecksumError(f"Unsupported algorithm in registry: {stored_entry.get('algorithm')}")

    current_hash = compute_file_sha256(file_path)
    stored_hash = stored_entry["hash"]

    if current_hash != stored_hash:
        raise ChecksumError(
            f"Integrity check failed for {relative_path}. "
            f"Expected: {stored_hash}, Found: {current_hash}"
        )

    return True
