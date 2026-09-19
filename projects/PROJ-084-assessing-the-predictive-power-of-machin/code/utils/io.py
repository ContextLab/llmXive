"""
I/O Utilities for robust file handling.
"""
import os
import hashlib
import logging
from pathlib import Path
from typing import Optional, Union, List, Iterator, Dict, Any, Callable, TypeVar
import pandas as pd
import pyarrow.parquet as pq

logger = logging.getLogger(__name__)

def get_file_size_mb(file_path: Path) -> float:
    """Get file size in MB."""
    if not file_path.exists():
        return 0.0
    return os.path.getsize(file_path) / (1024 * 1024)

def calculate_md5(file_path: Path) -> str:
    """Calculate MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def verify_checksum(file_path: Path, checksum_file: Path) -> bool:
    """Verify file checksum against a stored value."""
    if not checksum_file.exists():
        logger.warning(f"Checksum file not found: {checksum_file}")
        return False
    
    with open(checksum_file, 'r') as f:
        stored_checksum = f.read().strip()
    
    calculated = calculate_sha256(file_path)
    if calculated != stored_checksum:
        logger.error(f"Checksum mismatch for {file_path}. Expected: {stored_checksum}, Got: {calculated}")
        return False
    
    logger.info(f"Checksum verified for {file_path}")
    return True

def check_memory_limit(required_gb: float, max_limit_gb: float = 7.0) -> bool:
    """Check if required memory is within limits."""
    import psutil
    available = psutil.virtual_memory().available / (1024**3)
    return available >= required_gb

def load_parquet(file_path: Path, columns: Optional[List[str]] = None) -> pd.DataFrame:
    """Load a Parquet file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    return pd.read_parquet(file_path, columns=columns)

def load_csv(file_path: Path, **kwargs) -> pd.DataFrame:
    """Load a CSV file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    return pd.read_csv(file_path, **kwargs)

def save_parquet(df: pd.DataFrame, file_path: Path, compression: str = 'snappy'):
    """Save a DataFrame to Parquet."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(file_path, compression=compression, index=False)
    logger.info(f"Saved {len(df)} rows to {file_path}")

def save_csv(df: pd.DataFrame, file_path: Path):
    """Save a DataFrame to CSV."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(file_path, index=False)
    logger.info(f"Saved {len(df)} rows to {file_path}")

def process_in_batches(df: pd.DataFrame, batch_size: int) -> Iterator[pd.DataFrame]:
    """Iterate over a DataFrame in batches."""
    for start in range(0, len(df), batch_size):
        yield df.iloc[start:start + batch_size]

def validate_memory_requirement(df: pd.DataFrame, max_mb: int = 6000) -> bool:
    """Check if a DataFrame fits in memory."""
    size_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
    return size_mb < max_mb

__all__ = [
    'get_file_size_mb', 'calculate_md5', 'calculate_sha256', 'verify_checksum',
    'check_memory_limit', 'load_parquet', 'load_csv', 'save_parquet', 'save_csv',
    'process_in_batches', 'validate_memory_requirement'
]
