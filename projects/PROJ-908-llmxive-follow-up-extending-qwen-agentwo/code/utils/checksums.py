"""
Checksum utilities for data hygiene and source verification.

This module provides functions to compute and verify checksums (SHA-256)
for files and data streams to ensure data integrity and detect drift.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Union


def compute_file_sha256(file_path: Union[str, Path], chunk_size: int = 8192) -> str:
    """
    Compute the SHA-256 checksum of a file.

    Args:
        file_path: Path to the file to checksum.
        chunk_size: Size of chunks to read at a time (default 8KB).

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        PermissionError: If the file cannot be read.
    """
    sha256_hash = hashlib.sha256()
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256_hash.update(chunk)

    return sha256_hash.hexdigest()


def compute_string_sha256(data: str, encoding: str = "utf-8") -> str:
    """
    Compute the SHA-256 checksum of a string.

    Args:
        data: The string to checksum.
        encoding: String encoding (default utf-8).

    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    return hashlib.sha256(data.encode(encoding)).hexdigest()


def verify_file_checksum(
    file_path: Union[str, Path],
    expected_checksum: str,
    algorithm: str = "sha256"
) -> bool:
    """
    Verify a file's checksum against an expected value.

    Args:
        file_path: Path to the file.
        expected_checksum: Expected hexadecimal checksum string.
        algorithm: Hash algorithm to use (default 'sha256').

    Returns:
        True if the checksum matches, False otherwise.

    Raises:
        ValueError: If the algorithm is not supported.
        FileNotFoundError: If the file does not exist.
    """
    supported_algorithms = {"sha256", "sha512", "md5"}
    if algorithm.lower() not in supported_algorithms:
        raise ValueError(f"Unsupported algorithm: {algorithm}. Supported: {supported_algorithms}")

    hasher = hashlib.new(algorithm)
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)

    return hasher.hexdigest().lower() == expected_checksum.lower()


def generate_checksum_manifest(
    file_paths: List[Union[str, Path]],
    output_path: Optional[Union[str, Path]] = None,
    algorithm: str = "sha256"
) -> Dict[str, str]:
    """
    Generate a manifest of checksums for a list of files.

    Args:
        file_paths: List of file paths to checksum.
        output_path: Optional path to write the manifest as JSON.
        algorithm: Hash algorithm to use (default 'sha256').

    Returns:
        Dictionary mapping file paths (as strings) to their checksums.

    Raises:
        FileNotFoundError: If any file does not exist.
    """
    manifest = {}
    for file_path in file_paths:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        checksum = compute_file_sha256(path)
        manifest[str(path)] = checksum

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

    return manifest


def verify_checksum_manifest(
    manifest_path: Union[str, Path],
    algorithm: str = "sha256"
) -> Dict[str, bool]:
    """
    Verify files against a checksum manifest.

    Args:
        manifest_path: Path to the JSON manifest file.
        algorithm: Hash algorithm used in the manifest (default 'sha256').

    Returns:
        Dictionary mapping file paths to verification status (True/False).

    Raises:
        FileNotFoundError: If the manifest or any tracked file is missing.
        json.JSONDecodeError: If the manifest is malformed.
    """
    path = Path(manifest_path)
    if not path.exists():
        raise FileNotFoundError(f"Manifest not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    results = {}
    for file_str, expected_checksum in manifest.items():
        file_path = Path(file_str)
        if not file_path.exists():
            results[file_str] = False
            continue

        try:
            actual_checksum = compute_file_sha256(file_path, algorithm)
            results[file_str] = (actual_checksum.lower() == expected_checksum.lower())
        except Exception:
            results[file_str] = False

    return results


def check_code_drift(
    source_path: Union[str, Path],
    baseline_checksum: str,
    tolerance: float = 0.0
) -> bool:
    """
    Check if source code has drifted from a baseline checksum.

    This is used to detect unintended changes in source files during
    automated pipeline execution (e.g., after code generation steps).

    Args:
        source_path: Path to the source file to check.
        baseline_checksum: The expected SHA-256 checksum of the baseline.
        tolerance: Fraction of checksum difference allowed (currently unused,
                   as checksums are binary). Reserved for future hash-based
                   similarity metrics.

    Returns:
        True if the file matches the baseline (no drift), False otherwise.

    Raises:
        FileNotFoundError: If the source file does not exist.
    """
    if tolerance != 0.0:
        # Future extension: use fuzzy hashing (e.g., ssdeep) for tolerance
        pass

    actual_checksum = compute_file_sha256(source_path)
    return actual_checksum.lower() == baseline_checksum.lower()