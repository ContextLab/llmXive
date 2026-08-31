"""
Checksum verification utilities for data integrity.

This module provides functionality to verify file integrity against
a recorded manifest of checksums (SHA-256).
"""

import os
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional

from utils.logger import get_logger
from utils.exceptions import DataValidationError

logger = get_logger(__name__)

MANIFEST_FILENAME = "checksum_manifest.json"


def compute_file_checksum(file_path: str) -> str:
    """
    Compute the SHA-256 checksum of a file.

    Args:
        file_path: Path to the file to compute checksum for.

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        PermissionError: If the file cannot be read.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files efficiently
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def load_manifest(data_dir: str) -> Dict[str, str]:
    """
    Load the checksum manifest from the data directory.

    Args:
        data_dir: Path to the data directory containing the manifest.

    Returns:
        Dictionary mapping relative file paths to their expected checksums.

    Raises:
        FileNotFoundError: If the manifest file does not exist.
        json.JSONDecodeError: If the manifest is malformed.
    """
    manifest_path = Path(data_dir) / MANIFEST_FILENAME
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"Checksum manifest not found at {manifest_path}. "
            "Run setup_data_dirs.py to create the manifest."
        )
    
    with open(manifest_path, "r") as f:
        manifest_data = json.load(f)
    
    return manifest_data.get("files", {})


def verify_checksums(data_dir: str) -> bool:
    """
    Verify that all files in the data directory match their recorded checksums.

    This function:
    1. Loads the checksum manifest from {data_dir}/checksum_manifest.json
    2. Iterates through all registered files
    3. Computes the current SHA-256 hash for each file
    4. Compares against the stored hash

    Args:
        data_dir: Path to the data directory to verify.

    Returns:
        True if all files match their recorded checksums.

    Raises:
        DataValidationError: If any file is missing or has a checksum mismatch.
        FileNotFoundError: If the manifest file is missing.
    """
    data_path = Path(data_dir)
    
    if not data_path.exists():
        raise DataValidationError(f"Data directory does not exist: {data_dir}")

    logger.info(f"Verifying checksums for directory: {data_dir}")
    
    try:
        manifest = load_manifest(data_dir)
    except FileNotFoundError as e:
        raise DataValidationError(str(e)) from e
    except json.JSONDecodeError as e:
        raise DataValidationError(f"Invalid manifest format: {e}") from e

    if not manifest:
        logger.warning("Manifest is empty. Nothing to verify.")
        return True

    mismatches = []
    missing_files = []

    for relative_path, expected_hash in manifest.items():
        full_path = data_path / relative_path
        
        if not full_path.exists():
            missing_files.append(relative_path)
            logger.error(f"Missing file: {full_path}")
            continue

        try:
            actual_hash = compute_file_checksum(str(full_path))
            if actual_hash != expected_hash:
                mismatches.append({
                    "file": relative_path,
                    "expected": expected_hash,
                    "actual": actual_hash
                })
                logger.error(
                    f"Checksum mismatch for {relative_path}: "
                    f"expected {expected_hash[:16]}..., got {actual_hash[:16]}..."
                )
            else:
                logger.debug(f"Verified: {relative_path}")
        except (PermissionError, IOError) as e:
            mismatches.append({
                "file": relative_path,
                "error": str(e)
            })
            logger.error(f"Error reading file {relative_path}: {e}")

    if missing_files:
        raise DataValidationError(
            f"Verification failed: {len(missing_files)} file(s) missing: {missing_files}"
        )

    if mismatches:
        error_details = [
            f"{m['file']}: {m.get('error', 'hash mismatch')}" 
            for m in mismatches
        ]
        raise DataValidationError(
            f"Verification failed: {len(mismatches)} file(s) failed: {error_details}"
        )

    logger.info("All files verified successfully.")
    return True