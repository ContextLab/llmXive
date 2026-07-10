"""
Checksum utilities for data integrity verification.
Implements SHA-256 checksum generation and validation for dataset artifacts.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any

CHECKSUM_FILE = "data/.checksums.json"


def compute_sha256(file_path: str) -> str:
    """
    Compute SHA-256 checksum of a file.

    Args:
        file_path: Path to the file to checksum

    Returns:
        Hexadecimal string of the SHA-256 hash
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def save_checksums(checksums: Dict[str, str], output_path: Optional[str] = None) -> None:
    """
    Save checksums to a JSON file.

    Args:
        checksums: Dictionary mapping file paths to their checksums
        output_path: Optional custom output path (defaults to data/.checksums.json)
    """
    path = Path(output_path) if output_path else Path(CHECKSUM_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(checksums, f, indent=2)


def load_checksums(input_path: Optional[str] = None) -> Dict[str, str]:
    """
    Load checksums from a JSON file.

    Args:
        input_path: Optional custom input path (defaults to data/.checksums.json)

    Returns:
        Dictionary mapping file paths to their checksums, or empty dict if not found
    """
    path = Path(input_path) if input_path else Path(CHECKSUM_FILE)
    if not path.exists():
        return {}
    with open(path, "r") as f:
        return json.load(f)


def validate_file(file_path: str, expected_checksum: str) -> bool:
    """
    Validate a file against its expected checksum.

    Args:
        file_path: Path to the file to validate
        expected_checksum: Expected SHA-256 checksum

    Returns:
        True if checksum matches, False otherwise
    """
    actual_checksum = compute_sha256(file_path)
    return actual_checksum == expected_checksum


def validate_all_checksums() -> Dict[str, bool]:
    """
    Validate all files in the checksum registry.

    Returns:
        Dictionary mapping file paths to validation status (True/False)
    """
    checksums = load_checksums()
    results = {}
    for file_path, expected in checksums.items():
        if not os.path.exists(file_path):
            results[file_path] = False
        else:
            results[file_path] = validate_file(file_path, expected)
    return results


def register_file(file_path: str, output_path: Optional[str] = None) -> str:
    """
    Compute and register a checksum for a file.

    Args:
        file_path: Path to the file to register
        output_path: Optional custom output path for checksums

    Returns:
        The computed checksum
    """
    checksum = compute_sha256(file_path)
    existing = load_checksums(output_path)
    existing[file_path] = checksum
    save_checksums(existing, output_path)
    return checksum
