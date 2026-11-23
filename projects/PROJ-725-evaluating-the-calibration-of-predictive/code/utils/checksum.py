"""
Checksum utilities for artifact integrity verification.

Provides functions to compute SHA-256 hashes of files and verify
files against known checksums. This is critical for ensuring
reproducibility in the research pipeline.
"""

import hashlib
import os
from typing import Optional, Tuple

BUFFER_SIZE = 65536  # 64KB chunks for efficient reading


def compute_file_checksum(file_path: str, algorithm: str = "sha256") -> str:
    """
    Compute the checksum of a file.

    Reads the file in chunks to handle large files without loading them entirely into memory.

    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (default: 'sha256').

    Returns:
        Hexadecimal string representation of the checksum.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If an unsupported algorithm is requested.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    if algorithm not in hashlib.algorithms_available:
        raise ValueError(f"Unsupported algorithm: {algorithm}")

    hasher = hashlib.new(algorithm)

    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(BUFFER_SIZE)
            if not chunk:
                break
            hasher.update(chunk)

    return hasher.hexdigest()


def verify_file_checksum(
    file_path: str,
    expected_checksum: str,
    algorithm: str = "sha256",
) -> Tuple[bool, str]:
    """
    Verify a file's checksum against an expected value.

    Args:
        file_path: Path to the file.
        expected_checksum: The expected hexadecimal checksum string.
        algorithm: Hash algorithm to use.

    Returns:
        A tuple (is_valid, computed_checksum).
        is_valid is True if the computed checksum matches the expected one.
    """
    computed = compute_file_checksum(file_path, algorithm)
    # Normalize to lowercase for comparison
    return computed.lower() == expected_checksum.lower(), computed


def write_checksum_file(
    file_path: str,
    checksum_path: str,
    algorithm: str = "sha256",
) -> None:
    """
    Compute the checksum of a file and write it to a separate .checksum file.

    The checksum file will contain the algorithm and the hex digest.
    Format: "<algorithm>:<hexdigest>"

    Args:
        file_path: Path to the source file.
        checksum_path: Path where the checksum file will be written.
        algorithm: Hash algorithm to use.
    """
    checksum = compute_file_checksum(file_path, algorithm)
    with open(checksum_path, "w", encoding="utf-8") as f:
        f.write(f"{algorithm}:{checksum}\n")


def read_checksum_file(checksum_path: str) -> Tuple[str, str]:
    """
    Read a checksum file and return the algorithm and checksum.

    Args:
        checksum_path: Path to the checksum file.

    Returns:
        Tuple of (algorithm, checksum).

    Raises:
        ValueError: If the file format is invalid.
    """
    with open(checksum_path, "r", encoding="utf-8") as f:
        content = f.read().strip()

    if ":" not in content:
        raise ValueError(f"Invalid checksum file format: {checksum_path}")

    parts = content.split(":", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid checksum file format: {checksum_path}")

    return parts[0], parts[1]
