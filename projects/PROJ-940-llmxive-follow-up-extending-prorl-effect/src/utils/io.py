"""
Deterministic file I/O utilities for JSON and Parquet formats.

Provides functions to read/write data with checksum verification
to ensure reproducibility and data integrity.
"""

import json
import hashlib
import os
from typing import Any, Optional, Union
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq


def _calculate_checksum(file_path: Union[str, Path]) -> str:
    """
    Calculate SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def write_json(
    data: Any,
    output_path: Union[str, Path],
    ensure_dir: bool = True,
    indent: int = 2,
    sort_keys: bool = False
) -> dict:
    """
    Write data to a JSON file with checksum generation.
    
    Args:
        data: Python object to serialize (must be JSON-serializable).
        output_path: Path to the output JSON file.
        ensure_dir: If True, create parent directories if they don't exist.
        indent: Indentation level for pretty-printing.
        sort_keys: If True, sort keys alphabetically for deterministic output.
        
    Returns:
        Dictionary containing 'path', 'checksum', 'size_bytes', and 'records'.
        
    Raises:
        TypeError: If data is not JSON-serializable.
        IOError: If file cannot be written.
    """
    output_path = Path(output_path)
    
    if ensure_dir:
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, sort_keys=sort_keys, ensure_ascii=False)
    
    checksum = _calculate_checksum(output_path)
    size_bytes = output_path.stat().st_size
    records = len(data) if isinstance(data, list) else 1
    
    return {
        "path": str(output_path),
        "checksum": checksum,
        "size_bytes": size_bytes,
        "records": records
    }


def read_json(
    input_path: Union[str, Path],
    verify_checksum: Optional[str] = None
) -> Any:
    """
    Read data from a JSON file with optional checksum verification.
    
    Args:
        input_path: Path to the input JSON file.
        verify_checksum: Optional checksum to verify against.
        
    Returns:
        Deserialized Python object.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
        ValueError: If checksum verification fails.
    """
    input_path = Path(input_path)
    
    if not input_path.exists():
        raise FileNotFoundError(f"JSON file not found: {input_path}")
    
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    if verify_checksum is not None:
        actual_checksum = _calculate_checksum(input_path)
        if actual_checksum != verify_checksum:
            raise ValueError(
                f"Checksum verification failed for {input_path}. "
                f"Expected: {verify_checksum}, Got: {actual_checksum}"
            )
    
    return data


def write_parquet(
    df: pd.DataFrame,
    output_path: Union[str, Path],
    ensure_dir: bool = True,
    compression: str = "snappy"
) -> dict:
    """
    Write DataFrame to a Parquet file with checksum generation.
    
    Args:
        df: Pandas DataFrame to write.
        output_path: Path to the output Parquet file.
        ensure_dir: If True, create parent directories if they don't exist.
        compression: Compression codec ('snappy', 'gzip', 'brotli', 'lz4', 'zstd').
        
    Returns:
        Dictionary containing 'path', 'checksum', 'size_bytes', and 'records'.
        
    Raises:
        TypeError: If df is not a pandas DataFrame.
        IOError: If file cannot be written.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected pandas DataFrame, got {type(df).__name__}")
    
    output_path = Path(output_path)
    
    if ensure_dir:
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_parquet(
        output_path,
        engine="pyarrow",
        compression=compression,
        index=False
    )
    
    checksum = _calculate_checksum(output_path)
    size_bytes = output_path.stat().st_size
    records = len(df)
    
    return {
        "path": str(output_path),
        "checksum": checksum,
        "size_bytes": size_bytes,
        "records": records
    }


def read_parquet(
    input_path: Union[str, Path],
    verify_checksum: Optional[str] = None,
    columns: Optional[list[str]] = None
) -> pd.DataFrame:
    """
    Read data from a Parquet file with optional checksum verification.
    
    Args:
        input_path: Path to the input Parquet file.
        verify_checksum: Optional checksum to verify against.
        columns: Optional list of columns to load.
        
    Returns:
        Pandas DataFrame.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
        ValueError: If checksum verification fails.
    """
    input_path = Path(input_path)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Parquet file not found: {input_path}")
    
    df = pd.read_parquet(input_path, columns=columns, engine="pyarrow")
    
    if verify_checksum is not None:
        actual_checksum = _calculate_checksum(input_path)
        if actual_checksum != verify_checksum:
            raise ValueError(
                f"Checksum verification failed for {input_path}. "
                f"Expected: {verify_checksum}, Got: {actual_checksum}"
            )
    
    return df


def verify_file_checksum(
    file_path: Union[str, Path],
    expected_checksum: str
) -> bool:
    """
    Verify the checksum of a file against an expected value.
    
    Args:
        file_path: Path to the file.
        expected_checksum: Expected SHA-256 checksum.
        
    Returns:
        True if checksums match, False otherwise.
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    actual_checksum = _calculate_checksum(file_path)
    return actual_checksum == expected_checksum


def get_file_info(file_path: Union[str, Path]) -> dict:
    """
    Get metadata information about a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Dictionary containing 'path', 'checksum', 'size_bytes', 'modified_time',
        and 'extension'.
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    stat_info = file_path.stat()
    
    return {
        "path": str(file_path),
        "checksum": _calculate_checksum(file_path),
        "size_bytes": stat_info.st_size,
        "modified_time": stat_info.st_mtime,
        "extension": file_path.suffix
    }