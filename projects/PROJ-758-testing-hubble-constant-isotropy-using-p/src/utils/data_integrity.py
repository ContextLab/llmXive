"""
Data integrity utilities for raw data validation.

This module provides checksum verification and data validation functions
to ensure the integrity of raw datasets downloaded from external sources.
"""
import hashlib
import logging
from pathlib import Path
from typing import Optional, Tuple

from .logger import get_logger


def compute_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute the checksum of a file using the specified algorithm.

    Args:
        file_path: Path to the file to compute checksum for.
        algorithm: Hash algorithm to use (default: 'sha256').

    Returns:
        Hexadecimal string of the computed checksum.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    logger = get_logger(__name__)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        hasher = hashlib.new(algorithm)
    except ValueError as e:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}") from e

    logger.info(f"Computing {algorithm} checksum for {file_path}")
    
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files efficiently
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)

    checksum = hasher.hexdigest()
    logger.info(f"Checksum computed: {checksum}")
    return checksum


def verify_checksum(
    file_path: Path, 
    expected_checksum: str, 
    algorithm: str = "sha256"
) -> Tuple[bool, str]:
    """
    Verify a file's checksum against an expected value.

    Args:
        file_path: Path to the file to verify.
        expected_checksum: Expected checksum value (hex string).
        algorithm: Hash algorithm to use (default: 'sha256').

    Returns:
        Tuple of (is_valid, message) where is_valid is True if checksums match.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    logger = get_logger(__name__)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    computed = compute_checksum(file_path, algorithm)
    
    if computed.lower() == expected_checksum.lower():
        message = f"Checksum verification successful for {file_path.name}"
        logger.info(message)
        return True, message
    else:
        message = (
            f"Checksum verification FAILED for {file_path.name}. "
            f"Expected: {expected_checksum}, Computed: {computed}"
        )
        logger.error(message)
        return False, message


def validate_raw_data(
    data_dir: Path, 
    checksums_file: Optional[Path] = None
) -> bool:
    """
    Validate all raw data files in a directory against known checksums.

    Args:
        data_dir: Path to the directory containing raw data files.
        checksums_file: Optional path to a file containing checksums.
                        Expected format: one line per file as "checksum filepath".
                        If not provided, attempts to find a checksums file in the same directory.

    Returns:
        True if all validations pass, False otherwise.

    Raises:
        FileNotFoundError: If data directory or checksums file does not exist.
    """
    logger = get_logger(__name__)
    
    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")
    
    if not data_dir.is_dir():
        raise ValueError(f"Path is not a directory: {data_dir}")

    # Determine checksums file location
    if checksums_file is None:
        checksums_file = data_dir.parent / "checksums.txt"
        if not checksums_file.exists():
            checksums_file = data_dir / "checksums.txt"
    
    if not checksums_file.exists():
        logger.warning(f"No checksums file found at {checksums_file}. Skipping validation.")
        return True

    logger.info(f"Validating raw data in {data_dir} using checksums from {checksums_file}")
    
    all_valid = True
    
    with open(checksums_file, "r") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            parts = line.split(maxsplit=1)
            if len(parts) != 2:
                logger.warning(f"Skipping malformed line {line_num} in checksums file: {line}")
                continue
            
            expected_checksum, relative_path = parts
            file_path = data_dir / relative_path
            
            if not file_path.exists():
                logger.error(f"File not found for validation: {file_path}")
                all_valid = False
                continue
            
            is_valid, message = verify_checksum(file_path, expected_checksum)
            if not is_valid:
                all_valid = False

    if all_valid:
        logger.info("All raw data files validated successfully.")
    else:
        logger.error("Some raw data files failed validation.")
    
    return all_valid