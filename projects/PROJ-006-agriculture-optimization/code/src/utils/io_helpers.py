"""
I/O Helpers for strict file operations, checksum verification, and logging infrastructure.

This module provides robust wrappers for CSV, Parquet, and JSON I/O operations
that enforce schema compliance and data integrity. It also initializes the
project's logging infrastructure.
"""

import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Union, Dict, Any, Literal

import pandas as pd

# ---------------------------------------------------------------------------
# Logging Infrastructure Setup
# ---------------------------------------------------------------------------

def setup_logging(
    log_file: Optional[Union[str, Path]] = None,
    level: int = logging.INFO,
    project_name: str = "PROJ-006-agriculture-optimization"
) -> logging.Logger:
    """
    Configure the project logging infrastructure.

    Sets up a root logger with handlers for both console (stderr) and
    optional file output. Ensures consistent formatting and prevents
    duplicate handlers on re-entry.

    Args:
        log_file: Optional path to a log file. If None, only logs to console.
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
        project_name: Name prefix for the logger.

    Returns:
        The configured logger instance.
    """
    logger = logging.getLogger(project_name)
    logger.setLevel(level)

    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    # Formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, mode='a')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------

class FatalError(Exception):
    """
    Raised when a critical, unrecoverable error occurs (e.g., missing data,
    authentication failure, schema violation).
    """
    pass


class IntegrityError(Exception):
    """
    Raised when a file integrity check (checksum) fails or data is corrupted.
    """
    pass


# ---------------------------------------------------------------------------
# File I/O Wrappers
# ---------------------------------------------------------------------------

def _compute_checksum(file_path: Path, algorithm: str = 'sha256') -> str:
    """
    Compute the SHA-256 checksum of a file.

    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use.

    Returns:
        Hexadecimal digest string.
    """
    hasher = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)
    return hasher.hexdigest()


def read_csv_strict(
    path: Union[str, Path],
    required_columns: Optional[list[str]] = None,
    checksum_path: Optional[Union[str, Path]] = None
) -> pd.DataFrame:
    """
    Read a CSV file with strict validation.

    - Verifies file existence.
    - Optionally verifies checksum against a sidecar file.
    - Validates that required columns are present.
    - Raises FatalError or IntegrityError on failure.

    Args:
        path: Path to the CSV file.
        required_columns: List of column names that must exist.
        checksum_path: Path to a file containing the expected checksum.

    Returns:
        pandas DataFrame.

    Raises:
        FatalError: If file not found or missing required columns.
        IntegrityError: If checksum verification fails.
    """
    path = Path(path)
    if not path.exists():
        raise FatalError(f"File not found: {path}")

    # Checksum verification
    if checksum_path:
        checksum_path = Path(checksum_path)
        if checksum_path.exists():
            expected_hash = checksum_path.read_text().strip()
            actual_hash = _compute_checksum(path)
            if expected_hash != actual_hash:
                raise IntegrityError(
                    f"Checksum mismatch for {path}. "
                    f"Expected: {expected_hash}, Got: {actual_hash}"
                )
        else:
            # If checksum file is missing but expected, log a warning but proceed
            # depending on strictness requirements. Here we assume it's optional
            # if the file doesn't exist yet, but if it exists, it must match.
            pass

    try:
        df = pd.read_csv(path)
    except Exception as e:
        raise FatalError(f"Failed to parse CSV {path}: {e}")

    if required_columns:
        missing = set(required_columns) - set(df.columns)
        if missing:
            raise FatalError(f"Missing required columns in {path}: {missing}")

    return df


def write_csv_strict(
    df: pd.DataFrame,
    path: Union[str, Path],
    compute_checksum: bool = True
) -> None:
    """
    Write a DataFrame to CSV with optional checksum generation.

    Args:
        df: DataFrame to write.
        path: Output path.
        compute_checksum: If True, write a .sha256 sidecar file.

    Raises:
        FatalError: If write fails.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        df.to_csv(path, index=False)
    except Exception as e:
        raise FatalError(f"Failed to write CSV {path}: {e}")

    if compute_checksum:
        checksum_path = Path(str(path) + '.sha256')
        checksum = _compute_checksum(path)
        checksum_path.write_text(checksum)


def read_parquet_strict(
    path: Union[str, Path],
    required_columns: Optional[list[str]] = None,
    checksum_path: Optional[Union[str, Path]] = None
) -> pd.DataFrame:
    """
    Read a Parquet file with strict validation.

    Args:
        path: Path to the Parquet file.
        required_columns: List of column names that must exist.
        checksum_path: Path to a file containing the expected checksum.

    Returns:
        pandas DataFrame.

    Raises:
        FatalError: If file not found or missing required columns.
        IntegrityError: If checksum verification fails.
    """
    path = Path(path)
    if not path.exists():
        raise FatalError(f"File not found: {path}")

    # Checksum verification
    if checksum_path:
        checksum_path = Path(checksum_path)
        if checksum_path.exists():
            expected_hash = checksum_path.read_text().strip()
            actual_hash = _compute_checksum(path)
            if expected_hash != actual_hash:
                raise IntegrityError(
                    f"Checksum mismatch for {path}. "
                    f"Expected: {expected_hash}, Got: {actual_hash}"
                )

    try:
        df = pd.read_parquet(path)
    except Exception as e:
        raise FatalError(f"Failed to parse Parquet {path}: {e}")

    if required_columns:
        missing = set(required_columns) - set(df.columns)
        if missing:
            raise FatalError(f"Missing required columns in {path}: {missing}")

    return df


def write_parquet_strict(
    df: pd.DataFrame,
    path: Union[str, Path],
    compute_checksum: bool = True
) -> None:
    """
    Write a DataFrame to Parquet with optional checksum generation.

    Args:
        df: DataFrame to write.
        path: Output path.
        compute_checksum: If True, write a .sha256 sidecar file.

    Raises:
        FatalError: If write fails.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        df.to_parquet(path, index=False)
    except Exception as e:
        raise FatalError(f"Failed to write Parquet {path}: {e}")

    if compute_checksum:
        checksum_path = Path(str(path) + '.sha256')
        checksum = _compute_checksum(path)
        checksum_path.write_text(checksum)


def load_json_strict(
    path: Union[str, Path],
    required_keys: Optional[list[str]] = None
) -> Dict[str, Any]:
    """
    Load a JSON file with strict validation.

    Args:
        path: Path to the JSON file.
        required_keys: List of top-level keys that must exist.

    Returns:
        Parsed JSON as a dictionary.

    Raises:
        FatalError: If file not found, invalid JSON, or missing keys.
    """
    path = Path(path)
    if not path.exists():
        raise FatalError(f"File not found: {path}")

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise FatalError(f"Invalid JSON in {path}: {e}")
    except Exception as e:
        raise FatalError(f"Failed to read JSON {path}: {e}")

    if required_keys:
        missing = set(required_keys) - set(data.keys())
        if missing:
            raise FatalError(f"Missing required keys in {path}: {missing}")

    return data


def write_json_strict(
    data: Dict[str, Any],
    path: Union[str, Path],
    indent: int = 2,
    compute_checksum: bool = True
) -> None:
    """
    Write a dictionary to JSON with optional checksum generation.

    Args:
        data: Dictionary to write.
        path: Output path.
        indent: Indentation level for pretty printing.
        compute_checksum: If True, write a .sha256 sidecar file.

    Raises:
        FatalError: If write fails.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent)
    except Exception as e:
        raise FatalError(f"Failed to write JSON {path}: {e}")

    if compute_checksum:
        checksum_path = Path(str(path) + '.sha256')
        checksum = _compute_checksum(path)
        checksum_path.write_text(checksum)