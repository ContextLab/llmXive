"""
I/O utilities for loading and saving data with memory management.

This module provides functions for:
- Loading/saving Parquet and CSV files
- Calculating checksums (MD5, SHA256)
- Batch processing to manage memory
- Memory limit checking
"""
import os
import hashlib
import logging
from pathlib import Path
from typing import Optional, Union, List, Iterator, Dict, Any, Callable, TypeVar

import pandas as pd
import psutil

logger = logging.getLogger(__name__)

# Constants
MEMORY_LIMIT_GB = 7.0  # Maximum memory usage in GB


def get_file_size_mb(file_path: Union[str, Path]) -> float:
    """Get file size in megabytes."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return path.stat().st_size / (1024 * 1024)


def calculate_md5(file_path: Union[str, Path]) -> str:
    """Calculate MD5 checksum of a file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    md5_hash = hashlib.md5()
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            md5_hash.update(byte_block)
    return md5_hash.hexdigest()


def calculate_sha256(file_path: Union[str, Path]) -> str:
    """Calculate SHA256 checksum of a file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def verify_checksum(file_path: Union[str, Path], expected_checksum: str) -> bool:
    """
    Verify file checksum against expected value.
    
    Args:
        file_path: Path to the file
        expected_checksum: Expected checksum string
        
    Returns:
        True if checksum matches
        
    Raises:
        ValueError: If checksum doesn't match
    """
    actual_checksum = calculate_sha256(file_path)
    if actual_checksum != expected_checksum:
        raise ValueError(
            f"Checksum mismatch for {file_path}: "
            f"actual={actual_checksum}, expected={expected_checksum}"
        )
    return True


def check_memory_limit(limit_gb: float = MEMORY_LIMIT_GB) -> bool:
    """
    Check if current memory usage is within limit.
    
    Args:
        limit_gb: Memory limit in GB
        
    Returns:
        True if within limit, False otherwise
    """
    memory = psutil.virtual_memory()
    used_gb = memory.used / (1024 ** 3)
    
    if used_gb > limit_gb:
        logger.warning(f"Memory usage ({used_gb:.2f} GB) exceeds limit ({limit_gb} GB)")
        return False
    
    return True


def load_parquet(file_path: Union[str, Path], **kwargs) -> pd.DataFrame:
    """
    Load a Parquet file into a DataFrame.
    
    Args:
        file_path: Path to the Parquet file
        **kwargs: Additional arguments for pd.read_parquet
        
    Returns:
        Loaded DataFrame
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Parquet file not found: {path}")
    
    logger.info(f"Loading Parquet file: {path} ({get_file_size_mb(path):.2f} MB)")
    df = pd.read_parquet(path, **kwargs)
    logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")
    return df


def load_csv(file_path: Union[str, Path], **kwargs) -> pd.DataFrame:
    """
    Load a CSV file into a DataFrame.
    
    Args:
        file_path: Path to the CSV file
        **kwargs: Additional arguments for pd.read_csv
        
    Returns:
        Loaded DataFrame
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")
    
    logger.info(f"Loading CSV file: {path} ({get_file_size_mb(path):.2f} MB)")
    df = pd.read_csv(path, **kwargs)
    logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")
    return df


def save_parquet(df: pd.DataFrame, file_path: Union[str, Path], **kwargs) -> None:
    """
    Save a DataFrame to a Parquet file.
    
    Args:
        df: DataFrame to save
        file_path: Output path for Parquet file
        **kwargs: Additional arguments for df.to_parquet
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving Parquet file: {path} ({len(df)} rows)")
    df.to_parquet(path, **kwargs)
    logger.info(f"Saved {len(df)} rows to {path}")


def save_csv(df: pd.DataFrame, file_path: Union[str, Path], **kwargs) -> None:
    """
    Save a DataFrame to a CSV file.
    
    Args:
        df: DataFrame to save
        file_path: Output path for CSV file
        **kwargs: Additional arguments for df.to_csv
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving CSV file: {path} ({len(df)} rows)")
    df.to_csv(path, index=False, **kwargs)
    logger.info(f"Saved {len(df)} rows to {path}")


def process_in_batches(
    file_path: Union[str, Path],
    batch_size: int = 10000,
    **kwargs
) -> Iterator[pd.DataFrame]:
    """
    Process a Parquet file in batches to manage memory.
    
    Args:
        file_path: Path to the Parquet file
        batch_size: Number of rows per batch
        **kwargs: Additional arguments for pd.read_parquet
        
    Yields:
        DataFrame batches
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    logger.info(f"Processing {path} in batches of {batch_size}")
    
    # Use pyarrow for chunked reading
    import pyarrow.parquet as pq
    
    parquet_file = pq.ParquetFile(path)
    
    for batch in parquet_file.iter_batches(batch_size=batch_size):
        df = batch.to_pandas()
        yield df
        
        # Check memory periodically
        if not check_memory_limit():
            logger.warning("Memory limit reached, consider reducing batch size")


def validate_memory_requirement(df: pd.DataFrame, limit_gb: float = MEMORY_LIMIT_GB) -> bool:
    """
    Validate if a DataFrame fits within memory limit.
    
    Args:
        df: DataFrame to check
        limit_gb: Memory limit in GB
        
    Returns:
        True if DataFrame fits within limit
    """
    # Estimate memory usage
    estimated_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
    estimated_gb = estimated_mb / 1024
    
    if estimated_gb > limit_gb:
        logger.warning(
            f"DataFrame size ({estimated_gb:.2f} GB) exceeds limit ({limit_gb} GB)"
        )
        return False
    
    return True
