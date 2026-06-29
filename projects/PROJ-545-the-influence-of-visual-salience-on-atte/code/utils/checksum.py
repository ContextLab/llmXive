"""
Data checksumming utility for raw file verification.

This module provides functions to compute and verify SHA-256 checksums for
raw data files to ensure data integrity during ingestion and processing.
"""

import hashlib
import os
from pathlib import Path
from typing import Optional, Dict, Any

from .logger import get_logger, log_error_to_file

# Configure logger for this module
logger = get_logger(__name__)


def compute_file_sha256(file_path: Path, chunk_size: int = 8192) -> str:
    """
    Compute the SHA-256 checksum of a file.

    Args:
        file_path: Path to the file to hash.
        chunk_size: Size of chunks to read at a time (default 8KB).

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        PermissionError: If the file cannot be read.
        IOError: If an I/O error occurs during reading.
    """
    if not file_path.exists():
        error_msg = f"File not found: {file_path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    if not file_path.is_file():
        error_msg = f"Path is not a file: {file_path}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    sha256_hash = hashlib.sha256()

    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                sha256_hash.update(chunk)
    except PermissionError as e:
        error_msg = f"Permission denied reading file: {file_path}"
        logger.error(error_msg)
        log_error_to_file(error_msg, file_path.parent / "checksum_errors.log")
        raise
    except IOError as e:
        error_msg = f"I/O error reading file {file_path}: {str(e)}"
        logger.error(error_msg)
        log_error_to_file(error_msg, file_path.parent / "checksum_errors.log")
        raise

    return sha256_hash.hexdigest()


def verify_checksum(file_path: Path, expected_checksum: str) -> bool:
    """
    Verify that a file's checksum matches the expected value.

    Args:
        file_path: Path to the file to verify.
        expected_checksum: Expected SHA-256 hex string.

    Returns:
        True if checksums match, False otherwise.
    """
    try:
        actual_checksum = compute_file_sha256(file_path)
        is_valid = actual_checksum.lower() == expected_checksum.lower()

        if not is_valid:
            logger.warning(
                f"Checksum mismatch for {file_path.name}. "
                f"Expected: {expected_checksum}, Got: {actual_checksum}"
            )
        else:
            logger.info(f"Checksum verified for {file_path.name}")

        return is_valid

    except (FileNotFoundError, ValueError, PermissionError, IOError) as e:
        logger.error(f"Verification failed for {file_path}: {str(e)}")
        return False


def generate_checksum_manifest(file_paths: list[Path], output_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Generate a manifest of checksums for multiple files.

    Args:
        file_paths: List of file paths to checksum.
        output_path: Optional path to write the manifest as a text file.

    Returns:
        Dictionary mapping file names to their SHA-256 checksums.
    """
    manifest = {}

    for file_path in file_paths:
        try:
            checksum = compute_file_sha256(file_path)
            manifest[file_path.name] = checksum
            logger.info(f"Computed checksum for {file_path.name}: {checksum[:16]}...")
        except Exception as e:
            error_msg = f"Failed to compute checksum for {file_path}: {str(e)}"
            logger.error(error_msg)
            # Continue processing other files

    if output_path:
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                for filename, checksum in manifest.items():
                    f.write(f"{checksum}  {filename}\n")
            logger.info(f"Checksum manifest written to {output_path}")
        except IOError as e:
            error_msg = f"Failed to write manifest to {output_path}: {str(e)}"
            logger.error(error_msg)
            log_error_to_file(error_msg, output_path.parent / "checksum_errors.log")

    return manifest


def load_checksum_manifest(manifest_path: Path) -> Dict[str, str]:
    """
    Load a checksum manifest from a text file.

    Expected format:
        <sha256_hash>  <filename>
        <sha256_hash>  <filename>

    Args:
        manifest_path: Path to the manifest file.

    Returns:
        Dictionary mapping file names to their expected checksums.

    Raises:
        FileNotFoundError: If the manifest file does not exist.
        ValueError: If the manifest format is invalid.
    """
    if not manifest_path.exists():
        error_msg = f"Manifest file not found: {manifest_path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    manifest = {}

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                parts = line.split(None, 1)
                if len(parts) != 2:
                    error_msg = f"Invalid manifest format at line {line_num}: {line}"
                    logger.warning(error_msg)
                    continue

                checksum, filename = parts
                if len(checksum) != 64:
                    error_msg = f"Invalid checksum length at line {line_num}: {checksum}"
                    logger.warning(error_msg)
                    continue

                manifest[filename] = checksum

    except IOError as e:
        error_msg = f"Failed to read manifest {manifest_path}: {str(e)}"
        logger.error(error_msg)
        raise

    if not manifest:
        logger.warning("No valid entries found in manifest file")

    return manifest


def verify_manifest_files(manifest_path: Path, base_dir: Optional[Path] = None) -> Dict[str, bool]:
    """
    Verify all files listed in a manifest against their stored checksums.

    Args:
        manifest_path: Path to the checksum manifest file.
        base_dir: Base directory where files are located (defaults to manifest's parent).

    Returns:
        Dictionary mapping file names to verification status (True/False).
    """
    if base_dir is None:
        base_dir = manifest_path.parent

    manifest = load_checksum_manifest(manifest_path)
    results = {}

    for filename, expected_checksum in manifest.items():
        file_path = base_dir / filename
        results[filename] = verify_checksum(file_path, expected_checksum)

    # Log summary
    passed = sum(1 for status in results.values() if status)
    total = len(results)
    logger.info(f"Verification complete: {passed}/{total} files passed")

    return results