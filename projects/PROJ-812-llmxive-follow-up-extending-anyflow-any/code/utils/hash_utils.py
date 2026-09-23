"""
hash_utils.py
Utilities for SHA-256 checksumming of raw data and model weights.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Union

from .logging import get_logger

logger = get_logger(__name__)

CHUNK_SIZE = 1024 * 1024  # 1 MB chunks for reading large files


def compute_sha256(file_path: Union[str, Path]) -> str:
    """
    Compute the SHA-256 checksum of a file.

    Reads the file in chunks to handle large files (e.g., model weights)
    without exhausting memory.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 digest.

    Raises:
        FileNotFoundError: If the file does not exist.
        IsADirectoryError: If the path points to a directory.
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found for hashing: {path}")
    
    if path.is_dir():
        raise IsADirectoryError(f"Path is a directory, not a file: {path}")

    sha256_hash = hashlib.sha256()
    
    logger.debug(f"Computing SHA-256 for: {path}")
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
            sha256_hash.update(chunk)
    
    digest = sha256_hash.hexdigest()
    logger.debug(f"Computed SHA-256 for {path.name}: {digest[:16]}...")
    return digest


def verify_sha256(file_path: Union[str, Path], expected_hash: str) -> bool:
    """
    Verify a file's SHA-256 checksum against an expected value.

    Args:
        file_path: Path to the file to verify.
        expected_hash: The expected SHA-256 hex digest.

    Returns:
        True if the computed hash matches the expected hash, False otherwise.
    """
    computed = compute_sha256(file_path)
    # Normalize case for comparison
    computed = computed.lower()
    expected = expected_hash.lower()
    
    is_valid = computed == expected
    status = "valid" if is_valid else "invalid"
    logger.info(f"Verification for {Path(file_path).name}: {status}")
    return is_valid


def hash_directory(directory: Union[str, Path], pattern: Optional[str] = None) -> Dict[str, str]:
    """
    Compute SHA-256 hashes for all files in a directory.

    Args:
        directory: Path to the directory.
        pattern: Optional glob pattern to filter files (e.g., "*.pt", "*.csv").
                If None, all files are included.

    Returns:
        Dictionary mapping relative file paths to their SHA-256 hashes.
    """
    dir_path = Path(directory)
    if not dir_path.exists() or not dir_path.is_dir():
        raise NotADirectoryError(f"Directory not found: {dir_path}")

    hashes = {}
    files = list(dir_path.rglob("*")) if pattern is None else list(dir_path.rglob(pattern))
    
    # Filter out directories
    files = [f for f in files if f.is_file()]
    
    logger.info(f"Hashing {len(files)} files in {dir_path}")
    
    for file_path in files:
        try:
            file_hash = compute_sha256(file_path)
            rel_path = str(file_path.relative_to(dir_path))
            hashes[rel_path] = file_hash
        except Exception as e:
            logger.error(f"Failed to hash {file_path}: {e}")
            # Optionally raise or skip; here we skip and log
    
    return hashes


def save_checksums(hashes: Dict[str, str], output_path: Union[str, Path]) -> None:
    """
    Save a dictionary of file hashes to a JSON file.

    Args:
        hashes: Dictionary of {relative_path: sha256_hash}.
        output_path: Path to the output JSON file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(hashes, f, indent=2)
    
    logger.info(f"Saved checksums to {path}")


def load_checksums(checksum_path: Union[str, Path]) -> Dict[str, str]:
    """
    Load a dictionary of file hashes from a JSON file.

    Args:
        checksum_path: Path to the JSON file containing hashes.

    Returns:
        Dictionary of {relative_path: sha256_hash}.
    """
    path = Path(checksum_path)
    if not path.exists():
        raise FileNotFoundError(f"Checksum file not found: {path}")
    
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def verify_directory_integrity(directory: Union[str, Path], checksum_path: Union[str, Path]) -> List[str]:
    """
    Verify all files in a directory against a saved checksum file.

    Args:
        directory: Path to the directory containing the files.
        checksum_path: Path to the JSON file containing expected hashes.

    Returns:
        List of relative paths for files that failed verification (or were missing).
    """
    dir_path = Path(directory)
    expected_hashes = load_checksums(checksum_path)
    failures = []

    for rel_path, expected_hash in expected_hashes.items():
        full_path = dir_path / rel_path
        
        if not full_path.exists():
            logger.warning(f"Missing file during verification: {rel_path}")
            failures.append(rel_path)
            continue

        try:
            if not verify_sha256(full_path, expected_hash):
                logger.warning(f"Hash mismatch for: {rel_path}")
                failures.append(rel_path)
        except Exception as e:
            logger.error(f"Error verifying {rel_path}: {e}")
            failures.append(rel_path)

    if failures:
        logger.error(f"Integrity check failed for {len(failures)} files.")
    else:
        logger.info("Directory integrity check passed.")

    return failures
