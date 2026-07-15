"""
I/O Utilities for Data Hygiene and Directory Management.

This module provides utilities for:
- Ensuring the existence of required directory structures (raw vs processed).
- Verifying data integrity via checksums (SHA-256).
- Validating file presence against expected manifests.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Union

# Project root is assumed to be the parent of the 'code' directory
# or we rely on the caller to pass the correct base path.
# For robustness, we allow passing a base_path, defaulting to a relative resolution.
DEFAULT_BASE_PATH = Path(__file__).resolve().parent.parent.parent


def ensure_directory_structure(base_path: Optional[Union[str, Path]] = None) -> Dict[str, Path]:
    """
    Creates and returns paths for the required directory structure.

    Creates:
    - data/raw: For unmodified, downloaded source data.
    - data/processed: For cleaned, transformed, and feature-engineered data.

    Args:
        base_path: The root directory of the project. Defaults to resolving
                   relative to this file's location (project root).

    Returns:
        A dictionary mapping logical names to Path objects:
        {'root': ..., 'raw': ..., 'processed': ..., 'figures': ..., 'results': ...}
    """
    if base_path is None:
        base_path = DEFAULT_BASE_PATH
    else:
        base_path = Path(base_path)

    dirs = {
        'root': base_path,
        'data': base_path / 'data',
        'raw': base_path / 'data' / 'raw',
        'processed': base_path / 'data' / 'processed',
        'figures': base_path / 'figures',
        'results': base_path / 'results',
        'docs': base_path / 'docs',
        'code': base_path / 'code',
        'tests': base_path / 'tests',
    }

    for name, path in dirs.items():
        path.mkdir(parents=True, exist_ok=True)

    return dirs


def compute_file_checksum(file_path: Union[str, Path], algorithm: str = 'sha256') -> str:
    """
    Computes the cryptographic checksum of a file.

    Reads the file in chunks to handle large files without loading them entirely into memory.

    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (e.g., 'sha256', 'md5').

    Returns:
        Hexadecimal string of the checksum.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hasher = hashlib.new(algorithm)
    
    with open(file_path, 'rb') as f:
        # Read in chunks (64KB)
        for chunk in iter(lambda: f.read(65536), b''):
            hasher.update(chunk)
    
    return hasher.hexdigest()


def verify_checksum(file_path: Union[str, Path], expected_checksum: str, algorithm: str = 'sha256') -> bool:
    """
    Verifies a file's checksum against an expected value.

    Args:
        file_path: Path to the file.
        expected_checksum: The expected hexadecimal checksum string.
        algorithm: Hash algorithm to use.

    Returns:
        True if the computed checksum matches the expected one, False otherwise.
    """
    try:
        computed = compute_file_checksum(file_path, algorithm)
        return computed.lower() == expected_checksum.lower()
    except FileNotFoundError:
        return False


def load_checksum_manifest(manifest_path: Union[str, Path], base_path: Optional[Union[str, Path]] = None) -> Dict[str, str]:
    """
    Loads a JSON manifest containing expected checksums for data files.

    Expected JSON format:
    {
        "relative/path/to/file.csv": "sha256_hash_string",
        ...
    }

    Args:
        manifest_path: Path to the JSON manifest file.
        base_path: Base path to resolve relative paths within the manifest.

    Returns:
        Dictionary mapping relative file paths to their expected checksums.
    """
    manifest_path = Path(manifest_path)
    if not manifest_path.exists():
        return {}

    if base_path is None:
        base_path = DEFAULT_BASE_PATH
    else:
        base_path = Path(base_path)

    with open(manifest_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data


def validate_data_integrity(
    manifest_path: Union[str, Path],
    data_root: Optional[Union[str, Path]] = None,
    base_path: Optional[Union[str, Path]] = None
) -> Dict[str, Union[bool, str]]:
    """
    Validates the integrity of all files listed in a checksum manifest.

    Args:
        manifest_path: Path to the JSON manifest.
        data_root: Root directory where data files are located relative to the manifest keys.
                   If None, uses the project's 'data' directory.
        base_path: Project root for resolving paths.

    Returns:
        A dictionary with keys as file paths and values as:
        - 'valid': True if checksum matches.
        - 'missing': True if file is not found.
        - 'mismatch': True if checksum does not match.
        - 'error': Error message if computation failed.
    """
    if base_path is None:
        base_path = DEFAULT_BASE_PATH
    
    if data_root is None:
        data_root = Path(base_path) / 'data'
    else:
        data_root = Path(data_root)

    manifest = load_checksum_manifest(manifest_path, base_path)
    results = {}

    if not manifest:
        return {"status": "no_manifest", "message": "Manifest file empty or not found."}

    for rel_path, expected_hash in manifest.items():
        full_path = data_root / rel_path
        status_key = rel_path

        if not full_path.exists():
            results[status_key] = "missing"
            continue

        try:
            computed_hash = compute_file_checksum(full_path)
            if computed_hash.lower() == expected_hash.lower():
                results[status_key] = "valid"
            else:
                results[status_key] = "mismatch"
        except Exception as e:
            results[status_key] = f"error: {str(e)}"

    return results


def get_file_size_mb(file_path: Union[str, Path]) -> float:
    """
    Returns the size of a file in Megabytes.

    Args:
        file_path: Path to the file.

    Returns:
        File size in MB (float).
    """
    file_path = Path(file_path)
    if not file_path.exists():
        return 0.0
    return file_path.stat().st_size / (1024 * 1024)
