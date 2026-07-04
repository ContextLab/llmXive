"""
Utility functions for generating and verifying file checksums.
"""
import hashlib
import os
from typing import Optional, Dict, Any
from pathlib import Path


def generate_checksum(
    file_path: str,
    algorithm: str = "sha256",
    chunk_size: int = 8192
) -> str:
    """
    Generate a checksum for a file.

    Args:
        file_path: Path to the file to checksum.
        algorithm: Hash algorithm to use (default: 'sha256').
                   Supported: 'md5', 'sha1', 'sha256', 'sha512'.
        chunk_size: Size of chunks to read at a time (default: 8192 bytes).

    Returns:
        Hexadecimal string of the file's checksum.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If an unsupported algorithm is specified.
    """
    supported_algorithms = hashlib.algorithms_available
    if algorithm not in supported_algorithms:
        raise ValueError(f"Unsupported algorithm: {algorithm}. "
                       f"Available: {', '.join(sorted(supported_algorithms))}")

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hasher = hashlib.new(algorithm)

    with open(path, 'rb') as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)

    return hasher.hexdigest()


def verify_checksum(
    file_path: str,
    expected_checksum: str,
    algorithm: str = "sha256"
) -> bool:
    """
    Verify a file's checksum against an expected value.

    Args:
        file_path: Path to the file to verify.
        expected_checksum: The expected checksum value (hex string).
        algorithm: Hash algorithm used to generate the expected checksum.

    Returns:
        True if the checksum matches, False otherwise.
    """
    try:
        actual_checksum = generate_checksum(file_path, algorithm)
        return actual_checksum.lower() == expected_checksum.lower()
    except (FileNotFoundError, ValueError):
        return False


def generate_checksums_for_directory(
    directory_path: str,
    algorithm: str = "sha256",
    recursive: bool = True
) -> Dict[str, str]:
    """
    Generate checksums for all files in a directory.

    Args:
        directory_path: Path to the directory.
        algorithm: Hash algorithm to use.
        recursive: If True, process subdirectories (default: True).

    Returns:
        Dictionary mapping relative file paths to their checksums.
    """
    path = Path(directory_path)
    if not path.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory_path}")

    checksums = {}
    pattern = '**/*' if recursive else '*'

    for file_path in path.glob(pattern):
        if file_path.is_file():
            rel_path = file_path.relative_to(path)
            checksums[str(rel_path)] = generate_checksum(str(file_path), algorithm)

    return checksums


def write_checksum_file(
    file_path: str,
    output_path: str,
    algorithm: str = "sha256"
) -> str:
    """
    Generate a checksum for a file and write it to a sidecar file.

    Creates a file at `output_path` containing the checksum and filename.

    Args:
        file_path: Path to the file to checksum.
        output_path: Path where the checksum file will be written.
        algorithm: Hash algorithm to use.

    Returns:
        The generated checksum.
    """
    checksum = generate_checksum(file_path, algorithm)
    with open(output_path, 'w') as f:
        f.write(f"{checksum}  {os.path.basename(file_path)}\n")
    return checksum


def read_checksum_file(checksum_path: str) -> Dict[str, str]:
    """
    Read a checksum file and return a dictionary of checksums.

    Expects a format like:
        <checksum>  <filename>

    Args:
        checksum_path: Path to the checksum file.

    Returns:
        Dictionary mapping filenames to their checksums.
    """
    checksums = {}
    with open(checksum_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split(None, 1)  # Split on whitespace, max 2 parts
            if len(parts) == 2:
                checksum, filename = parts
                checksums[filename] = checksum
    return checksums