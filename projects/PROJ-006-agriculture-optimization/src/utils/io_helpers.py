"""
I/O Helpers for strict CSV/Parquet I/O and checksum verification.

This module provides robust, type-safe functions for reading and writing
CSV and Parquet files with integrity checks (SHA-256). It enforces strict
validation to prevent silent data corruption or schema drift.

Key Features:
- Strict reading: Raises exceptions on malformed data, missing columns, or type mismatches.
- Checksum verification: Validates file integrity on read and generates checksums on write.
- Atomic writes: Ensures files are written completely before renaming.
- FatalError/IntegrityError: Custom exceptions for clear failure modes.
"""

import hashlib
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Optional, Union, Dict, Any, List, Literal

import pandas as pd
import pyarrow.parquet as pq

# Configure logger
logger = logging.getLogger(__name__)

class FatalError(Exception):
    """
    Raised when a critical, unrecoverable error occurs (e.g., missing real data,
    invalid configuration, or schema violation that halts execution).
    """
    pass

class IntegrityError(Exception):
    """
    Raised when data integrity checks fail (e.g., checksum mismatch,
    corrupted file, or schema violation).
    """
    pass

def _calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def _write_atomic(file_path: Path, content: bytes) -> None:
    """
    Write content to a file atomically.
    Writes to a temp file first, then renames to avoid partial writes.
    """
    dir_path = file_path.parent
    dir_path.mkdir(parents=True, exist_ok=True)

    fd, temp_path = tempfile.mkstemp(dir=dir_path, prefix=".tmp_")
    try:
        with os.fdopen(fd, 'wb') as tmp:
            tmp.write(content)
        os.replace(temp_path, file_path)
    except Exception:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise

def read_csv_strict(
    file_path: Union[str, Path],
    required_columns: Optional[List[str]] = None,
    dtype_spec: Optional[Dict[str, Any]] = None,
    checksum: Optional[str] = None
) -> pd.DataFrame:
    """
    Read a CSV file with strict validation.

    Args:
        file_path: Path to the CSV file.
        required_columns: List of columns that MUST exist.
        dtype_spec: Dictionary mapping column names to expected dtypes.
        checksum: Expected SHA-256 checksum of the file.

    Returns:
        pd.DataFrame: The validated DataFrame.

    Raises:
        FatalError: If file does not exist or is unreadable.
        IntegrityError: If checksum mismatch or schema violation.
    """
    path = Path(file_path)
    if not path.exists():
        raise FatalError(f"File not found: {file_path}")

    if checksum:
        actual_checksum = _calculate_sha256(path)
        if actual_checksum != checksum:
            raise IntegrityError(
                f"Checksum mismatch for {file_path}. "
                f"Expected: {checksum}, Got: {actual_checksum}"
            )

    try:
        df = pd.read_csv(path)
    except Exception as e:
        raise FatalError(f"Failed to read CSV {file_path}: {e}")

    if required_columns:
        missing = set(required_columns) - set(df.columns)
        if missing:
            raise IntegrityError(
                f"Missing required columns in {file_path}: {missing}"
            )

    if dtype_spec:
        for col, expected_type in dtype_spec.items():
            if col in df.columns:
                if not pd.api.types.is_dtype_equal(df[col].dtype, expected_type):
                    # Attempt safe conversion if possible, otherwise raise
                    try:
                        df[col] = df[col].astype(expected_type)
                    except Exception:
                        raise IntegrityError(
                            f"Type mismatch for column '{col}' in {file_path}. "
                            f"Expected {expected_type}, got {df[col].dtype}"
                        )

    return df

def write_csv_strict(
    df: pd.DataFrame,
    file_path: Union[str, Path],
    checksum_file: Optional[Union[str, Path]] = None
) -> str:
    """
    Write a DataFrame to CSV strictly.

    Args:
        df: DataFrame to write.
        file_path: Target path.
        checksum_file: Optional path to write the checksum file (.sha256).

    Returns:
        str: The calculated SHA-256 checksum of the written file.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Write to buffer first to calculate hash
    csv_content = df.to_csv(index=False).encode('utf-8')
    checksum = hashlib.sha256(csv_content).hexdigest()

    _write_atomic(path, csv_content)
    logger.info(f"Wrote CSV to {path} (checksum: {checksum})")

    if checksum_file:
        ck_path = Path(checksum_file)
        ck_path.parent.mkdir(parents=True, exist_ok=True)
        with open(ck_path, 'w') as f:
            f.write(checksum)
        logger.debug(f"Wrote checksum to {ck_path}")

    return checksum

def read_parquet_strict(
    file_path: Union[str, Path],
    required_columns: Optional[List[str]] = None,
    checksum: Optional[str] = None
) -> pd.DataFrame:
    """
    Read a Parquet file with strict validation.

    Args:
        file_path: Path to the Parquet file.
        required_columns: List of columns that MUST exist.
        checksum: Expected SHA-256 checksum of the file.

    Returns:
        pd.DataFrame: The validated DataFrame.

    Raises:
        FatalError: If file does not exist or is unreadable.
        IntegrityError: If checksum mismatch or schema violation.
    """
    path = Path(file_path)
    if not path.exists():
        raise FatalError(f"File not found: {file_path}")

    if checksum:
        actual_checksum = _calculate_sha256(path)
        if actual_checksum != checksum:
            raise IntegrityError(
                f"Checksum mismatch for {file_path}. "
                f"Expected: {checksum}, Got: {actual_checksum}"
            )

    try:
        table = pq.read_table(path)
        df = table.to_pandas()
    except Exception as e:
        raise FatalError(f"Failed to read Parquet {file_path}: {e}")

    if required_columns:
        missing = set(required_columns) - set(df.columns)
        if missing:
            raise IntegrityError(
                f"Missing required columns in {file_path}: {missing}"
            )

    return df

def write_parquet_strict(
    df: pd.DataFrame,
    file_path: Union[str, Path],
    checksum_file: Optional[Union[str, Path]] = None
) -> str:
    """
    Write a DataFrame to Parquet strictly.

    Args:
        df: DataFrame to write.
        file_path: Target path.
        checksum_file: Optional path to write the checksum file (.sha256).

    Returns:
        str: The calculated SHA-256 checksum of the written file.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Write to buffer to calculate hash
    import pyarrow as pa
    table = pa.Table.from_pandas(df)
    sink = pa.BufferOutputStream()
    pq.write_table(table, sink)
    buffer = sink.getvalue()
    content = buffer.to_pybytes()
    checksum = hashlib.sha256(content).hexdigest()

    _write_atomic(path, content)
    logger.info(f"Wrote Parquet to {path} (checksum: {checksum})")

    if checksum_file:
        ck_path = Path(checksum_file)
        ck_path.parent.mkdir(parents=True, exist_ok=True)
        with open(ck_path, 'w') as f:
            f.write(checksum)
        logger.debug(f"Wrote checksum to {ck_path}")

    return checksum

def load_json_strict(
    file_path: Union[str, Path],
    required_keys: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Load a JSON file with strict validation.

    Args:
        file_path: Path to the JSON file.
        required_keys: List of top-level keys that MUST exist.

    Returns:
        Dict[str, Any]: The loaded JSON data.

    Raises:
        FatalError: If file does not exist or is invalid JSON.
        IntegrityError: If required keys are missing.
    """
    path = Path(file_path)
    if not path.exists():
        raise FatalError(f"File not found: {file_path}")

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise FatalError(f"Invalid JSON in {file_path}: {e}")
    except Exception as e:
        raise FatalError(f"Failed to read JSON {file_path}: {e}")

    if not isinstance(data, dict):
        raise IntegrityError(f"JSON in {file_path} must be an object at the root.")

    if required_keys:
        missing = set(required_keys) - set(data.keys())
        if missing:
            raise IntegrityError(
                f"Missing required keys in {file_path}: {missing}"
            )

    return data

def write_json_strict(
    data: Dict[str, Any],
    file_path: Union[str, Path],
    checksum_file: Optional[Union[str, Path]] = None
) -> str:
    """
    Write data to a JSON file strictly.

    Args:
        data: Dictionary to write.
        file_path: Target path.
        checksum_file: Optional path to write the checksum file (.sha256).

    Returns:
        str: The calculated SHA-256 checksum of the written file.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    json_content = json.dumps(data, indent=2, ensure_ascii=False).encode('utf-8')
    checksum = hashlib.sha256(json_content).hexdigest()

    _write_atomic(path, json_content)
    logger.info(f"Wrote JSON to {path} (checksum: {checksum})")

    if checksum_file:
        ck_path = Path(checksum_file)
        ck_path.parent.mkdir(parents=True, exist_ok=True)
        with open(ck_path, 'w') as f:
            f.write(checksum)
        logger.debug(f"Wrote checksum to {ck_path}")

    return checksum
