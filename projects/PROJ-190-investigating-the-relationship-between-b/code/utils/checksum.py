"""
Checksum utilities for data integrity verification.

Provides SHA-256 checksumming for files and directories to ensure
data integrity throughout the pipeline.
"""
import hashlib
import os
from pathlib import Path
from typing import Dict, List, Optional, Union

from .logging import get_logger

logger = get_logger(__name__)


def compute_file_sha256(file_path: Union[str, Path], chunk_size: int = 8192) -> str:
    """
    Compute the SHA-256 checksum of a single file.

    Args:
        file_path: Path to the file to checksum.
        chunk_size: Size of chunks to read at a time (default 8KB).

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        PermissionError: If the file cannot be read.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    sha256_hash = hashlib.sha256()
    logger.debug(f"Computing SHA-256 for: {file_path}")

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256_hash.update(chunk)

    result = sha256_hash.hexdigest()
    logger.debug(f"SHA-256 for {file_path.name}: {result}")
    return result


def compute_directory_checksums(
    directory: Union[str, Path],
    recursive: bool = True,
    extensions: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Compute SHA-256 checksums for all files in a directory.

    Args:
        directory: Path to the directory to scan.
        recursive: If True, scan subdirectories (default True).
        extensions: Optional list of file extensions to include (e.g., ['.csv', '.nii']).
                   If None, all files are included.

    Returns:
        Dictionary mapping relative file paths to their SHA-256 checksums.

    Raises:
        NotADirectoryError: If the path is not a directory.
    """
    dir_path = Path(directory)
    if not dir_path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {dir_path}")

    checksums: Dict[str, str] = {}
    logger.info(f"Computing checksums for directory: {dir_path}")

    if recursive:
        file_iter = dir_path.rglob("*")
    else:
        file_iter = dir_path.glob("*")

    for file_path in file_iter:
        if file_path.is_file():
            if extensions is not None:
                if file_path.suffix.lower() not in [ext.lower() for ext in extensions]:
                    continue

            try:
                rel_path = file_path.relative_to(dir_path)
                checksum = compute_file_sha256(file_path)
                checksums[str(rel_path)] = checksum
            except Exception as e:
                logger.error(f"Failed to checksum {file_path}: {e}")

    logger.info(f"Computed {len(checksums)} checksums for {dir_path}")
    return checksums


def verify_checksum(file_path: Union[str, Path], expected_checksum: str) -> bool:
    """
    Verify a file's SHA-256 checksum against an expected value.

    Args:
        file_path: Path to the file to verify.
        expected_checksum: Expected SHA-256 hex string.

    Returns:
        True if checksum matches, False otherwise.
    """
    actual_checksum = compute_file_sha256(file_path)
    is_valid = actual_checksum == expected_checksum.lower()

    if not is_valid:
        logger.warning(
            f"Checksum mismatch for {file_path}. "
            f"Expected: {expected_checksum}, Got: {actual_checksum}"
        )
    else:
        logger.debug(f"Checksum verified for {file_path}")

    return is_valid


def save_checksums(
    checksums: Dict[str, str],
    output_path: Union[str, Path]
) -> None:
    """
    Save checksums to a text file in a simple format.

    Format: <checksum>  <relative_path>
    (Two spaces between hash and path, compatible with sha256sum)

    Args:
        checksums: Dictionary of relative paths to checksums.
        output_path: Path to the output file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        for rel_path, checksum in sorted(checksums.items()):
            f.write(f"{checksum}  {rel_path}\n")

    logger.info(f"Saved {len(checksums)} checksums to {output_path}")


def load_checksums(checksum_path: Union[str, Path]) -> Dict[str, str]:
    """
    Load checksums from a text file.

    Expected format: <checksum>  <relative_path>

    Args:
        checksum_path: Path to the checksum file.

    Returns:
        Dictionary of relative paths to checksums.
    """
    checksum_path = Path(checksum_path)
    if not checksum_path.exists():
        raise FileNotFoundError(f"Checksum file not found: {checksum_path}")

    checksums: Dict[str, str] = {}

    with open(checksum_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split("  ", 1)
            if len(parts) == 2:
                checksum, rel_path = parts
                checksums[rel_path] = checksum.strip()
            else:
                logger.warning(f"Skipping malformed checksum line: {line}")

    logger.info(f"Loaded {len(checksums)} checksums from {checksum_path}")
    return checksums


def verify_directory_against_checksums(
    directory: Union[str, Path],
    checksum_path: Union[str, Path]
) -> bool:
    """
    Verify all files in a directory against a stored checksum file.

    Args:
        directory: Path to the directory to verify.
        checksum_path: Path to the checksum file.

    Returns:
        True if all files match their stored checksums, False otherwise.
    """
    checksums = load_checksums(checksum_path)
    dir_path = Path(directory)
    all_valid = True

    for rel_path, expected_checksum in checksums.items():
        file_path = dir_path / rel_path
        if not file_path.exists():
            logger.error(f"File missing during verification: {file_path}")
            all_valid = False
            continue

        if not verify_checksum(file_path, expected_checksum):
            all_valid = False

    if all_valid:
        logger.info("Directory verification passed: all checksums match.")
    else:
        logger.error("Directory verification failed: some checksums do not match.")

    return all_valid
