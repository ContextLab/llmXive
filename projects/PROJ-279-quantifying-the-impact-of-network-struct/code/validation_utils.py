"""
validation_utils.py

Utility functions for checksum verification and file integrity checks.
Implements Constitution Principle III: Data Integrity and Verification.
"""

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Dict, Optional, Tuple, List, Union

# Configure logger for this module
logger = logging.getLogger(__name__)

CHECKSUM_ALGORITHM = "sha256"
MANIFEST_FILENAME = "manifest.json"


def compute_file_checksum(file_path: Union[str, Path], algorithm: str = CHECKSUM_ALGORITHM) -> str:
    """
    Compute the cryptographic checksum (hash) of a file.

    Args:
        file_path: Path to the file to hash.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hexadecimal string of the file's checksum.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If an unsupported algorithm is requested.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found for checksum calculation: {path}")

    if algorithm not in hashlib.algorithms_available:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")

    hasher = hashlib.new(algorithm)
    
    # Read file in chunks to handle large files (e.g., MD trajectories)
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except IOError as e:
        logger.error(f"IOError while reading file {path} for checksum: {e}")
        raise


def verify_file_integrity(
    file_path: Union[str, Path], 
    expected_checksum: str, 
    algorithm: str = CHECKSUM_ALGORITHM
) -> bool:
    """
    Verify a file's integrity by comparing its computed checksum against an expected value.

    Args:
        file_path: Path to the file to verify.
        expected_checksum: The expected hexadecimal checksum string.
        algorithm: Hash algorithm to use.

    Returns:
        True if the checksum matches, False otherwise.
    """
    path = Path(file_path)
    if not path.exists():
        logger.error(f"File missing during integrity check: {path}")
        return False

    try:
        actual_checksum = compute_file_checksum(path, algorithm)
        if actual_checksum.lower() == expected_checksum.lower():
            logger.debug(f"Integrity check passed for {path}")
            return True
        else:
            logger.error(
                f"Integrity check FAILED for {path}. "
                f"Expected: {expected_checksum}, Got: {actual_checksum}"
            )
            return False
    except Exception as e:
        logger.error(f"Error during integrity verification for {path}: {e}")
        return False


def create_manifest(
    file_paths: List[Union[str, Path]], 
    output_path: Union[str, Path], 
    algorithm: str = CHECKSUM_ALGORITHM
) -> Dict[str, str]:
    """
    Generate a manifest file containing checksums for a list of files.

    Args:
        file_paths: List of file paths to include in the manifest.
        output_path: Path where the manifest JSON will be saved.
        algorithm: Hash algorithm to use.

    Returns:
        Dictionary mapping relative file paths to their checksums.
    """
    manifest_dir = Path(output_path).parent
    manifest_dir.mkdir(parents=True, exist_ok=True)

    manifest_data = {
        "algorithm": algorithm,
        "files": {}
    }

    for file_path in file_paths:
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"Skipping non-existent file in manifest creation: {path}")
            continue

        checksum = compute_file_checksum(path, algorithm)
        # Store relative path from the project root or the manifest's directory?
        # Usually relative to the project root or the data directory. 
        # We'll store the absolute path converted to string for clarity, 
        # or relative if it's within the same tree. Let's use relative to current dir 
        # if possible, otherwise absolute.
        try:
            rel_path = path.relative_to(Path.cwd())
        except ValueError:
            rel_path = path

        manifest_data["files"][str(rel_path)] = checksum
        logger.info(f"Added {rel_path} with checksum {checksum[:16]}... to manifest")

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)
        logger.info(f"Manifest saved to {output_path}")
    except IOError as e:
        logger.error(f"Failed to write manifest to {output_path}: {e}")
        raise

    return manifest_data["files"]


def verify_manifest(
    manifest_path: Union[str, Path],
    base_dir: Optional[Union[str, Path]] = None
) -> Tuple[bool, Dict[str, str]]:
    """
    Verify all files listed in a manifest against their recorded checksums.

    Args:
        manifest_path: Path to the manifest JSON file.
        base_dir: Optional base directory to resolve relative paths in the manifest.

    Returns:
        Tuple of (all_valid: bool, failed_files: Dict[filename, reason])
        - all_valid: True if all files pass verification.
        - failed_files: Dictionary of files that failed, with reason ("missing", "checksum_mismatch").
    """
    path = Path(manifest_path)
    if not path.exists():
        raise FileNotFoundError(f"Manifest file not found: {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in manifest {path}: {e}")

    algorithm = manifest_data.get("algorithm", CHECKSUM_ALGORITHM)
    files = manifest_data.get("files", {})

    if base_dir:
        base_dir = Path(base_dir)
    else:
        base_dir = Path.cwd()

    failed_files = {}
    all_valid = True

    for rel_path_str, expected_checksum in files.items():
        # Resolve path
        if Path(rel_path_str).is_absolute():
            current_path = Path(rel_path_str)
        else:
            current_path = base_dir / rel_path_str

        if not current_path.exists():
            failed_files[str(rel_path_str)] = "missing"
            all_valid = False
            logger.error(f"File missing in manifest verification: {current_path}")
            continue

        is_valid = verify_file_integrity(current_path, expected_checksum, algorithm)
        if not is_valid:
            failed_files[str(rel_path_str)] = "checksum_mismatch"
            all_valid = False

    return all_valid, failed_files


def check_file_age(file_path: Union[str, Path], max_age_seconds: int) -> bool:
    """
    Check if a file is older than a specified age in seconds.

    Args:
        file_path: Path to the file.
        max_age_seconds: Maximum allowed age in seconds.

    Returns:
        True if the file is within the age limit (or doesn't exist, handled as False),
        False if it is older.
    """
    path = Path(file_path)
    if not path.exists():
        return False

    try:
        mtime = path.stat().st_mtime
        current_time = os.path.getctime(path) # Note: ctime is creation time on Windows, mtime on Linux. 
                                              # For age, we usually want mtime.
        # Re-evaluating: os.path.getmtime is the standard way to get modification time.
        mtime = path.stat().st_mtime
        age = os.path.getmtime(path) # This returns timestamp, not age.
        # Correct logic:
        current_ts = os.path.getmtime(path) # Wait, os.path.getmtime returns the mtime timestamp.
        # We need current time.
        import time
        now = time.time()
        age = now - mtime
        
        if age > max_age_seconds:
            logger.warning(f"File {path} is too old ({age:.0f}s > {max_age_seconds}s)")
            return False
        return True
    except OSError as e:
        logger.error(f"Error checking file age for {path}: {e}")
        return False

# Alias for consistency with task description
verify_checksum = verify_file_integrity