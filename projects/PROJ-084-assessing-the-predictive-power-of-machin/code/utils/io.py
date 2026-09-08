"""
I/O utilities for data loading and saving.

Provides robust functions for loading/saving Parquet and CSV files,
checksumming, and batch processing to manage memory constraints.
"""
import os
import hashlib
import logging
from pathlib import Path
from typing import Optional, Union, List, Iterator, Dict, Any, Callable, TypeVar
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_file_size_mb(file_path: Path) -> float:
    """Get file size in megabytes."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    size_bytes = os.path.getsize(file_path)
    return size_bytes / (1024 * 1024)

def calculate_md5(file_path: Path) -> str:
    """Calculate MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def verify_checksum(file_path: Path, expected_checksum: str, algorithm: str = 'md5') -> bool:
    """
    Verify file checksum.
    
    Args:
        file_path: Path to file to verify
        expected_checksum: Expected checksum value
        algorithm: Checksum algorithm ('md5' or 'sha256')
        
    Returns:
        True if checksum matches
        
    Raises:
        ValueError: If checksum doesn't match
    """
    if algorithm == 'md5':
        actual_checksum = calculate_md5(file_path)
    elif algorithm == 'sha256':
        # Use SHA256 function from sanitize module if needed
        import hashlib
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        actual_checksum = sha256_hash.hexdigest()
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")
    
    if actual_checksum != expected_checksum:
        raise ValueError(f"Checksum mismatch: expected {expected_checksum}, got {actual_checksum}")
    
    logger.info(f"Checksum verified for {file_path.name}")
    return True

def check_memory_limit(max_memory_gb: float = 7.0) -> bool:
    """
    Check if available memory is within limit.
    
    Args:
        max_memory_gb: Maximum allowed memory in GB
        
    Returns:
        True if within limit, False otherwise
    """
    try:
        import psutil
        available_gb = psutil.virtual_memory().available / (1024 ** 3)
        if available_gb < max_memory_gb:
            logger.warning(f"Available memory ({available_gb:.2f} GB) is below limit ({max_memory_gb} GB)")
            return False
        return True
    except ImportError:
        logger.warning("psutil not available, skipping memory check")
        return True

def load_parquet(
    file_path: Union[str, Path],
    columns: Optional[List[str]] = None,
    chunk_size: Optional[int] = None
) -> Union[pd.DataFrame, Iterator[pd.DataFrame]]:
    """
    Load Parquet file with optional column selection and chunking.
    
    Args:
        file_path: Path to parquet file
        columns: Optional list of columns to load
        chunk_size: If provided, return iterator of DataFrames
        
    Returns:
        DataFrame or iterator of DataFrames
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Parquet file not found: {file_path}")
    
    logger.info(f"Loading parquet: {file_path}")
    
    if chunk_size:
        # Return iterator for large files
        def parquet_iterator():
            for chunk in pd.read_parquet(file_path, columns=columns, chunksize=chunk_size):
                yield chunk
        return parquet_iterator()
    else:
        df = pd.read_parquet(file_path, columns=columns)
        logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")
        return df

def load_csv(
    file_path: Union[str, Path],
    columns: Optional[List[str]] = None,
    chunk_size: Optional[int] = None
) -> Union[pd.DataFrame, Iterator[pd.DataFrame]]:
    """
    Load CSV file with optional column selection and chunking.
    
    Args:
        file_path: Path to CSV file
        columns: Optional list of columns to load
        chunk_size: If provided, return iterator of DataFrames
        
    Returns:
        DataFrame or iterator of DataFrames
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")
    
    logger.info(f"Loading CSV: {file_path}")
    
    if chunk_size:
        def csv_iterator():
            for chunk in pd.read_csv(file_path, usecols=columns, chunksize=chunk_size):
                yield chunk
        return csv_iterator()
    else:
        df = pd.read_csv(file_path, usecols=columns)
        logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")
        return df

def save_parquet(
    df: pd.DataFrame,
    file_path: Union[str, Path],
    compression: str = 'snappy'
) -> None:
    """
    Save DataFrame to Parquet file.
    
    Args:
        df: DataFrame to save
        file_path: Output path
        compression: Compression algorithm
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving parquet: {file_path} ({len(df)} rows)")
    df.to_parquet(file_path, compression=compression, index=False)
    logger.info(f"Saved {file_path}")

def save_csv(
    df: pd.DataFrame,
    file_path: Union[str, Path],
    index: bool = False
) -> None:
    """
    Save DataFrame to CSV file.
    
    Args:
        df: DataFrame to save
        file_path: Output path
        index: Whether to write index
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving CSV: {file_path} ({len(df)} rows)")
    df.to_csv(file_path, index=index)
    logger.info(f"Saved {file_path}")

def process_in_batches(
    df: pd.DataFrame,
    batch_size: int,
    processor: Callable[[pd.DataFrame], pd.DataFrame]
) -> pd.DataFrame:
    """
    Process large DataFrame in batches to manage memory.
    
    Args:
        df: Input DataFrame
        batch_size: Number of rows per batch
        processor: Function to apply to each batch
        
    Returns:
        Concatenated results from all batches
    """
    logger.info(f"Processing {len(df)} rows in batches of {batch_size}")
    results = []
    
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i+batch_size]
        logger.debug(f"Processing batch {i//batch_size + 1}")
        result = processor(batch)
        results.append(result)
    
    return pd.concat(results, ignore_index=True)

def validate_memory_requirement(df: pd.DataFrame, max_memory_gb: float = 7.0) -> bool:
    """
    Estimate if DataFrame fits in memory.
    
    Args:
        df: DataFrame to check
        max_memory_gb: Maximum allowed memory
        
    Returns:
        True if DataFrame fits, False otherwise
    """
    estimated_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
    estimated_gb = estimated_mb / 1024
    
    if estimated_gb > max_memory_gb:
        logger.warning(f"DataFrame size ({estimated_gb:.2f} GB) exceeds limit ({max_memory_gb} GB)")
        return False
    
    logger.info(f"DataFrame size: {estimated_gb:.2f} GB (within {max_memory_gb} GB limit)")
    return True