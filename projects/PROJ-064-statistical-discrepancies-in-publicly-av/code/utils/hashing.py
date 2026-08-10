"""
Content hashing utility for artifacts.

Provides functions to compute and verify SHA-256 checksums for data files
to ensure reproducibility and integrity of the research pipeline.
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union

from ..logger import get_logger
from ..exceptions import DiscrepancyError

logger = get_logger(__name__)

CHUNK_SIZE = 1024 * 1024  # 1 MB chunks for streaming large files

def compute_file_hash(
    file_path: Union[str, Path],
    algorithm: str = "sha256",
    chunk_size: int = CHUNK_SIZE
) -> str:
    """
    Compute the cryptographic hash of a file.

    Args:
        file_path: Path to the file to hash.
        algorithm: Hash algorithm to use (default: sha256).
        chunk_size: Size of chunks to read for large files.

    Returns:
        Hexadecimal digest string of the file hash.

    Raises:
        DiscrepancyError: If the file does not exist or cannot be read.
        ValueError: If the algorithm is not supported.
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise DiscrepancyError(f"File not found for hashing: {file_path}")

    if not file_path.is_file():
        raise DiscrepancyError(f"Path is not a file: {file_path}")

    try:
        hasher = hashlib.new(algorithm)
    except ValueError as e:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}") from e

    logger.debug(f"Computing {algorithm} hash for {file_path}")

    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)

    digest = hasher.hexdigest()
    logger.debug(f"Hash computed: {digest[:16]}...")
    return digest

def compute_directory_hash(
    dir_path: Union[str, Path],
    algorithm: str = "sha256",
    recursive: bool = True,
    exclude_patterns: Optional[list] = None
) -> Dict[str, str]:
    """
    Compute hashes for all files in a directory.

    Args:
        dir_path: Path to the directory.
        algorithm: Hash algorithm to use.
        recursive: Whether to recurse into subdirectories.
        exclude_patterns: List of glob patterns to exclude.

    Returns:
        Dictionary mapping relative file paths to their hex hashes.

    Raises:
        DiscrepancyError: If the directory does not exist.
    """
    dir_path = Path(dir_path)

    if not dir_path.exists():
        raise DiscrepancyError(f"Directory not found: {dir_path}")

    if not dir_path.is_dir():
        raise DiscrepancyError(f"Path is not a directory: {dir_path}")

    hashes = {}
    exclude_patterns = exclude_patterns or []

    def should_exclude(file_path: Path) -> bool:
        rel_path = str(file_path.relative_to(dir_path))
        return any(
            file_path.match(pattern) or rel_path.match(pattern)
            for pattern in exclude_patterns
        )

    logger.info(f"Computing hashes for directory: {dir_path}")

    if recursive:
        files = sorted(dir_path.rglob("*"))
    else:
        files = sorted(dir_path.glob("*"))

    for file_path in files:
        if file_path.is_file() and not should_exclude(file_path):
            try:
                rel_path = file_path.relative_to(dir_path)
                hashes[str(rel_path)] = compute_file_hash(file_path, algorithm)
            except DiscrepancyError as e:
                logger.warning(f"Skipping {file_path}: {e}")

    logger.info(f"Computed {len(hashes)} file hashes")
    return hashes

def save_checksums(
    hash_data: Dict[str, str],
    output_path: Union[str, Path]
) -> None:
    """
    Save hash data to a JSON file.

    Args:
        hash_data: Dictionary of file paths to hashes.
        output_path: Path to save the JSON checksum file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    manifest = {
        "algorithm": "sha256",
        "files": hash_data
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)

    logger.info(f"Checksums saved to {output_path}")

def load_checksums(
    checksum_path: Union[str, Path]
) -> Dict[str, str]:
    """
    Load hash data from a JSON file.

    Args:
        checksum_path: Path to the JSON checksum file.

    Returns:
        Dictionary of file paths to hashes.

    Raises:
        DiscrepancyError: If the file cannot be read or parsed.
    """
    checksum_path = Path(checksum_path)

    if not checksum_path.exists():
        raise DiscrepancyError(f"Checksum file not found: {checksum_path}")

    try:
        with open(checksum_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        return manifest.get("files", {})
    except json.JSONDecodeError as e:
        raise DiscrepancyError(f"Invalid JSON in checksum file: {checksum_path}") from e

def verify_file_hash(
    file_path: Union[str, Path],
    expected_hash: str,
    algorithm: str = "sha256"
) -> bool:
    """
    Verify a file's hash against an expected value.

    Args:
        file_path: Path to the file to verify.
        expected_hash: Expected hexadecimal hash string.
        algorithm: Hash algorithm to use.

    Returns:
        True if the hash matches, False otherwise.
    """
    actual_hash = compute_file_hash(file_path, algorithm)
    return actual_hash == expected_hash

def verify_directory_checksums(
    dir_path: Union[str, Path],
    checksum_path: Union[str, Path],
    strict: bool = False
) -> Dict[str, bool]:
    """
    Verify all files in a directory against a checksum manifest.

    Args:
        dir_path: Base directory containing the files.
        checksum_path: Path to the JSON checksum manifest.
        strict: If True, fail if any file is missing or hash mismatch.

    Returns:
        Dictionary mapping file paths to verification status (True/False).

    Raises:
        DiscrepancyError: If verification fails in strict mode.
    """
    dir_path = Path(dir_path)
    checksums = load_checksums(checksum_path)
    results = {}
    failures = []

    for rel_path, expected_hash in checksums.items():
        file_path = dir_path / rel_path
        if file_path.exists():
            if verify_file_hash(file_path, expected_hash):
                results[rel_path] = True
            else:
                results[rel_path] = False
                failures.append(rel_path)
                logger.warning(f"Hash mismatch for {rel_path}")
        else:
            results[rel_path] = False
            failures.append(rel_path)
            logger.warning(f"File missing: {rel_path}")

    if strict and failures:
        raise DiscrepancyError(
            f"Verification failed for {len(failures)} files: {failures}"
        )

    return results