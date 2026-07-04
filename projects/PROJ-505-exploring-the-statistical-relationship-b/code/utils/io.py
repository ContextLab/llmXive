"""
I/O utilities for checksumming and parquet loading.

This module provides functions to:
- Compute and verify MD5 checksums for data integrity.
- Load Parquet files with schema validation and error handling.
"""

import hashlib
import os
from pathlib import Path
from typing import Optional

import pandas as pd
import pyarrow.parquet as pq


def compute_md5(file_path: str) -> str:
    """
    Compute the MD5 checksum of a file.

    Args:
        file_path: Path to the file to checksum.

    Returns:
        Hexadecimal string of the MD5 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hash_md5 = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def verify_md5(file_path: str, expected_md5: str) -> bool:
    """
    Verify a file's MD5 checksum against an expected value.

    Args:
        file_path: Path to the file.
        expected_md5: Expected hexadecimal MD5 string.

    Returns:
        True if the checksum matches, False otherwise.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    actual = compute_md5(file_path)
    return actual == expected_md5.lower()


def load_parquet(file_path: str, columns: Optional[list[str]] = None) -> pd.DataFrame:
    """
    Load a Parquet file into a pandas DataFrame.

    Args:
        file_path: Path to the Parquet file.
        columns: Optional list of columns to load. If None, loads all.

    Returns:
        pandas DataFrame containing the data.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is not a valid Parquet file.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Parquet file not found: {file_path}")

    try:
        if columns:
            return pd.read_parquet(path, columns=columns)
        return pd.read_parquet(path)
    except Exception as e:
        raise ValueError(f"Failed to load Parquet file {file_path}: {e}") from e


def save_parquet(df: pd.DataFrame, file_path: str, compression: str = "snappy") -> None:
    """
    Save a pandas DataFrame to a Parquet file.

    Args:
        df: DataFrame to save.
        file_path: Destination path for the Parquet file.
        compression: Compression codec (e.g., 'snappy', 'gzip', 'zstd').
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, compression=compression, index=False)