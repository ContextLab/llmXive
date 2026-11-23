"""
I/O Helpers: Strict CSV/Parquet I/O with checksum verification.

This module provides robust file reading and writing functions that enforce
data integrity through checksums and strict schema validation.
"""
import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, Union

import pandas as pd
import pyarrow.parquet as pq

# Configure logging
logger = logging.getLogger(__name__)


class FatalError(Exception):
    """Critical error that should stop execution immediately."""
    pass


class IntegrityError(Exception):
    """Data integrity verification failed."""
    pass


def _compute_checksum(file_path: Path) -> str:
    """Compute MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def _ensure_directory(file_path: Path) -> None:
    """Ensure the directory for a file exists."""
    file_path.parent.mkdir(parents=True, exist_ok=True)


def read_csv_strict(
    file_path: Union[str, Path],
    expected_columns: Optional[list] = None,
    checksum: Optional[str] = None
) -> pd.DataFrame:
    """
    Read a CSV file with strict validation.
    
    Args:
        file_path: Path to the CSV file.
        expected_columns: Optional list of expected column names.
        checksum: Optional expected MD5 checksum.
        
    Returns:
        DataFrame with the CSV contents.
        
    Raises:
        FatalError: If file does not exist or is unreadable.
        IntegrityError: If checksum mismatch or column mismatch.
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FatalError(f"CSV file not found: {path}")
    
    try:
        df = pd.read_csv(path)
    except Exception as e:
        raise FatalError(f"Failed to read CSV {path}: {e}")
    
    if checksum:
        actual_checksum = _compute_checksum(path)
        if actual_checksum != checksum:
            raise IntegrityError(
                f"Checksum mismatch for {path}: expected {checksum}, got {actual_checksum}"
            )
    
    if expected_columns:
        missing = set(expected_columns) - set(df.columns)
        if missing:
            raise IntegrityError(
                f"CSV {path} missing expected columns: {missing}"
            )
    
    logger.info(f"Successfully read CSV: {path} ({len(df)} rows)")
    return df


def write_csv_strict(
    df: pd.DataFrame,
    file_path: Union[str, Path],
    index: bool = False
) -> str:
    """
    Write a DataFrame to CSV with strict validation.
    
    Args:
        df: DataFrame to write.
        file_path: Output path.
        index: Whether to write row index.
        
    Returns:
        MD5 checksum of the written file.
        
    Raises:
        FatalError: If write fails.
    """
    path = Path(file_path)
    _ensure_directory(path)
    
    try:
        df.to_csv(path, index=index)
    except Exception as e:
        raise FatalError(f"Failed to write CSV {path}: {e}")
    
    checksum = _compute_checksum(path)
    logger.info(f"Successfully wrote CSV: {path} ({len(df)} rows), checksum: {checksum}")
    return checksum


def read_parquet_strict(
    file_path: Union[str, Path],
    expected_columns: Optional[list] = None,
    checksum: Optional[str] = None
) -> pd.DataFrame:
    """
    Read a Parquet file with strict validation.
    
    Args:
        file_path: Path to the Parquet file.
        expected_columns: Optional list of expected column names.
        checksum: Optional expected MD5 checksum.
        
    Returns:
        DataFrame with the Parquet contents.
        
    Raises:
        FatalError: If file does not exist or is unreadable.
        IntegrityError: If checksum mismatch or column mismatch.
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FatalError(f"Parquet file not found: {path}")
    
    try:
        df = pd.read_parquet(path)
    except Exception as e:
        raise FatalError(f"Failed to read Parquet {path}: {e}")
    
    if checksum:
        actual_checksum = _compute_checksum(path)
        if actual_checksum != checksum:
            raise IntegrityError(
                f"Checksum mismatch for {path}: expected {checksum}, got {actual_checksum}"
            )
    
    if expected_columns:
        missing = set(expected_columns) - set(df.columns)
        if missing:
            raise IntegrityError(
                f"Parquet {path} missing expected columns: {missing}"
            )
    
    logger.info(f"Successfully read Parquet: {path} ({len(df)} rows)")
    return df


def write_parquet_strict(
    df: pd.DataFrame,
    file_path: Union[str, Path],
    index: bool = False
) -> str:
    """
    Write a DataFrame to Parquet with strict validation.
    
    Args:
        df: DataFrame to write.
        file_path: Output path.
        index: Whether to write row index.
        
    Returns:
        MD5 checksum of the written file.
        
    Raises:
        FatalError: If write fails.
    """
    path = Path(file_path)
    _ensure_directory(path)
    
    try:
        df.to_parquet(path, index=index)
    except Exception as e:
        raise FatalError(f"Failed to write Parquet {path}: {e}")
    
    checksum = _compute_checksum(path)
    logger.info(f"Successfully wrote Parquet: {path} ({len(df)} rows), checksum: {checksum}")
    return checksum


def load_json_strict(
    file_path: Union[str, Path],
    expected_keys: Optional[list] = None
) -> Dict[str, Any]:
    """
    Load a JSON file with strict validation.
    
    Args:
        file_path: Path to the JSON file.
        expected_keys: Optional list of expected top-level keys.
        
    Returns:
        Parsed JSON as a dictionary.
        
    Raises:
        FatalError: If file does not exist or is invalid JSON.
        IntegrityError: If expected keys are missing.
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FatalError(f"JSON file not found: {path}")
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise FatalError(f"Invalid JSON in {path}: {e}")
    except Exception as e:
        raise FatalError(f"Failed to read JSON {path}: {e}")
    
    if expected_keys:
        missing = set(expected_keys) - set(data.keys())
        if missing:
            raise IntegrityError(
                f"JSON {path} missing expected keys: {missing}"
            )
    
    logger.info(f"Successfully loaded JSON: {path}")
    return data


def write_json_strict(
    data: Dict[str, Any],
    file_path: Union[str, Path],
    indent: int = 2
) -> str:
    """
    Write a dictionary to JSON with strict validation.
    
    Args:
        data: Dictionary to write.
        file_path: Output path.
        indent: Indentation level for pretty printing.
        
    Returns:
        MD5 checksum of the written file.
        
    Raises:
        FatalError: If write fails.
    """
    path = Path(file_path)
    _ensure_directory(path)
    
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent)
    except Exception as e:
        raise FatalError(f"Failed to write JSON {path}: {e}")
    
    checksum = _compute_checksum(path)
    logger.info(f"Successfully wrote JSON: {path}, checksum: {checksum}")
    return checksum