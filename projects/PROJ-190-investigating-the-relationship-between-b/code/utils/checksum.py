"""
Utility module for SHA-256 checksumming of data files and directories.
Implements T008: Setup checksumming utility.
"""
import hashlib
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Union

from .logging import get_logger

logger = get_logger(__name__)


def compute_file_sha256(file_path: Union[str, Path]) -> str:
    """
    Compute the SHA-256 hash of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hexadecimal string of the SHA-256 hash.

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
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        raise IOError(f"Error reading file {file_path}: {e}")


def compute_directory_checksums(dir_path: Union[str, Path], recursive: bool = True) -> Dict[str, str]:
    """
    Compute SHA-256 hashes for all files in a directory.

    Args:
        dir_path: Path to the directory.
        recursive: If True, scan subdirectories.

    Returns:
        Dictionary mapping relative file paths to their SHA-256 hashes.
    """
    dir_path = Path(dir_path)
    if not dir_path.is_dir():
        raise NotADirectoryError(f"Not a directory: {dir_path}")

    checksums = {}
    files = []
    
    if recursive:
        files = list(dir_path.rglob("*"))
    else:
        files = list(dir_path.glob("*"))

    for file_path in files:
        if file_path.is_file():
            try:
                rel_path = file_path.relative_to(dir_path)
                checksums[str(rel_path)] = compute_file_sha256(file_path)
            except Exception as e:
                logger.warning(f"Skipping {file_path} due to error: {e}")

    return checksums


def verify_checksum(file_path: Union[str, Path], expected_hash: str) -> bool:
    """
    Verify a file's SHA-256 hash against an expected value.

    Args:
        file_path: Path to the file.
        expected_hash: Expected SHA-256 hex string.

    Returns:
        True if hashes match, False otherwise.
    """
    actual_hash = compute_file_sha256(file_path)
    return actual_hash.lower() == expected_hash.lower()


def save_checksums(checksums: Dict[str, str], output_path: Union[str, Path]) -> None:
    """
    Save a dictionary of checksums to a JSON file.

    Args:
        checksums: Dictionary of {relative_path: hash}.
        output_path: Path to the output JSON file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(checksums, f, indent=2)
    logger.info(f"Checksums saved to {output_path}")


def load_checksums(input_path: Union[str, Path]) -> Dict[str, str]:
    """
    Load checksums from a JSON file.

    Args:
        input_path: Path to the JSON file.

    Returns:
        Dictionary of {relative_path: hash}.
    """
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Checksum file not found: {input_path}")

    with open(input_path, "r") as f:
        return json.load(f)


def verify_directory_against_checksums(
    dir_path: Union[str, Path],
    checksum_file: Union[str, Path],
    strict: bool = True
) -> bool:
    """
    Verify all files in a directory against a saved checksum manifest.

    Args:
        dir_path: Root directory to verify.
        checksum_file: Path to the JSON file containing expected checksums.
        strict: If True, fail if any file is missing or hash mismatch. 
               If False, log warnings but return False only on critical failure.

    Returns:
        True if all files match, False otherwise.
    """
    dir_path = Path(dir_path)
    checksums = load_checksums(checksum_file)
    all_good = True

    for rel_path, expected_hash in checksums.items():
        file_path = dir_path / rel_path
        
        if not file_path.exists():
            logger.error(f"Missing file: {rel_path}")
            all_good = False
            if strict:
                return False
            continue

        try:
            actual_hash = compute_file_sha256(file_path)
            if actual_hash != expected_hash:
                logger.error(f"Hash mismatch for {rel_path}: expected {expected_hash}, got {actual_hash}")
                all_good = False
                if strict:
                    return False
            else:
                logger.debug(f"Verified: {rel_path}")
        except Exception as e:
            logger.error(f"Error verifying {rel_path}: {e}")
            all_good = False
            if strict:
                return False

    return all_good
