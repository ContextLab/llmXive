"""
Robust I/O utilities for the llmXive project.
Handles Parquet/CSV loading with memory management, checksumming, and batch processing.
"""
import os
import hashlib
import logging
from pathlib import Path
from typing import Optional, Union, List, Iterator, Dict, Any

import pandas as pd
import pyarrow.parquet as pq

from code.config import DATA_RAW_DIR, DATA_PROCESSED_DIR, DATA_RESULTS_DIR

logger = logging.getLogger(__name__)

# Constants for memory management
CHUNK_SIZE = 100000  # Rows per chunk for batch processing
MEMORY_LIMIT_GB = 7.0
MEMORY_LIMIT_BYTES = MEMORY_LIMIT_GB * 1024**3


def calculate_md5(file_path: Union[str, Path]) -> str:
    """
    Calculate the MD5 checksum of a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Hexadecimal MD5 checksum string.
    """
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def verify_checksum(file_path: Union[str, Path], expected_md5: str) -> bool:
    """
    Verify a file's MD5 checksum against an expected value.
    
    Args:
        file_path: Path to the file.
        expected_md5: Expected MD5 checksum.
        
    Returns:
        True if checksum matches, False otherwise.
    """
    actual_md5 = calculate_md5(file_path)
    if actual_md5 != expected_md5:
        logger.error(
            f"Checksum mismatch for {file_path}. "
            f"Expected: {expected_md5}, Got: {actual_md5}"
        )
        return False
    logger.info(f"Checksum verified for {file_path}")
    return True


def load_parquet(
    file_path: Union[str, Path],
    columns: Optional[List[str]] = None,
    chunksize: Optional[int] = None,
    use_memory_map: bool = True
) -> Union[pd.DataFrame, Iterator[pd.DataFrame]]:
    """
    Load a Parquet file with optional column selection and chunking for memory efficiency.
    
    Args:
        file_path: Path to the Parquet file.
        columns: Optional list of columns to load.
        chunksize: If provided, returns an iterator of DataFrames instead of a single DataFrame.
        use_memory_map: Whether to use memory mapping for large files.
        
    Returns:
        A pandas DataFrame or an iterator of DataFrames if chunksize is specified.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or corrupted.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    logger.info(f"Loading Parquet file: {file_path}")
    
    try:
        if chunksize:
            parquet_file = pq.ParquetFile(path)
            return parquet_file.iter_batches(batch_size=chunksize)
        else:
            df = pd.read_parquet(
                path,
                columns=columns,
                use_memory_map=use_memory_map,
                engine='pyarrow'
            )
            if df.empty:
                logger.warning(f"Loaded empty DataFrame from {file_path}")
            logger.info(f"Loaded {len(df)} rows from {file_path}")
            return df
    except Exception as e:
        logger.error(f"Failed to load Parquet file {file_path}: {e}")
        raise


def load_csv(
    file_path: Union[str, Path],
    columns: Optional[List[str]] = None,
    chunksize: Optional[int] = None,
    dtype: Optional[Dict[str, Any]] = None
) -> Union[pd.DataFrame, Iterator[pd.DataFrame]]:
    """
    Load a CSV file with optional column selection and chunking for memory efficiency.
    
    Args:
        file_path: Path to the CSV file.
        columns: Optional list of columns to load.
        chunksize: If provided, returns an iterator of DataFrames.
        dtype: Optional dictionary of data types for columns.
        
    Returns:
        A pandas DataFrame or an iterator of DataFrames if chunksize is specified.
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    logger.info(f"Loading CSV file: {file_path}")
    
    try:
        if chunksize:
            return pd.read_csv(
                path,
                usecols=columns,
                chunksize=chunksize,
                dtype=dtype
            )
        else:
            df = pd.read_csv(
                path,
                usecols=columns,
                dtype=dtype
            )
            if df.empty:
                logger.warning(f"Loaded empty DataFrame from {file_path}")
            logger.info(f"Loaded {len(df)} rows from {file_path}")
            return df
    except Exception as e:
        logger.error(f"Failed to load CSV file {file_path}: {e}")
        raise


def save_parquet(
    df: pd.DataFrame,
    file_path: Union[str, Path],
    compression: str = 'snappy'
) -> None:
    """
    Save a DataFrame to a Parquet file.
    
    Args:
        df: The DataFrame to save.
        file_path: Path to save the Parquet file.
        compression: Compression codec to use.
        
    Raises:
        OSError: If the file cannot be written.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving Parquet file: {file_path} ({len(df)} rows)")
    try:
        df.to_parquet(
            path,
            compression=compression,
            index=False,
            engine='pyarrow'
        )
    except Exception as e:
        logger.error(f"Failed to save Parquet file {file_path}: {e}")
        raise


def save_csv(
    df: pd.DataFrame,
    file_path: Union[str, Path],
    index: bool = False
) -> None:
    """
    Save a DataFrame to a CSV file.
    
    Args:
        df: The DataFrame to save.
        file_path: Path to save the CSV file.
        index: Whether to write row indices.
        
    Raises:
        OSError: If the file cannot be written.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving CSV file: {file_path} ({len(df)} rows)")
    try:
        df.to_csv(path, index=index)
    except Exception as e:
        logger.error(f"Failed to save CSV file {file_path}: {e}")
        raise


def process_in_batches(
    file_path: Union[str, Path],
    file_type: str,
    process_func,
    chunksize: int = CHUNK_SIZE,
    **kwargs
) -> List[pd.DataFrame]:
    """
    Process a large file in batches to manage memory usage.
    
    Args:
        file_path: Path to the input file.
        file_type: 'parquet' or 'csv'.
        process_func: A function to apply to each batch (DataFrame -> DataFrame).
        chunksize: Number of rows per batch.
        **kwargs: Additional arguments for the loader.
        
    Returns:
        A list of processed DataFrames (one per batch).
    """
    if file_type == 'parquet':
        loader = lambda: load_parquet(file_path, chunksize=chunksize, **kwargs)
    elif file_type == 'csv':
        loader = lambda: load_csv(file_path, chunksize=chunksize, **kwargs)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")
    
    logger.info(f"Processing {file_path} in batches of {chunksize} rows...")
    results = []
    total_rows = 0
    
    batch_iterator = loader()
    for i, batch in enumerate(batch_iterator):
        # Handle pyarrow RecordBatch for parquet
        if isinstance(batch, pq.RecordBatch):
            batch = batch.to_pandas()
        
        total_rows += len(batch)
        logger.debug(f"Processing batch {i+1} ({len(batch)} rows)...")
        
        processed_batch = process_func(batch)
        results.append(processed_batch)
        
        # Explicitly delete batch to free memory
        del batch
        
    logger.info(f"Processed {total_rows} total rows in {len(results)} batches.")
    return results


def get_file_size_mb(file_path: Union[str, Path]) -> float:
    """
    Get the size of a file in megabytes.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        File size in MB.
    """
    return Path(file_path).stat().st_size / (1024 * 1024)


def estimate_memory_usage(df: pd.DataFrame) -> float:
    """
    Estimate the memory usage of a DataFrame in megabytes.
    
    Args:
        df: The DataFrame to check.
        
    Returns:
        Estimated memory usage in MB.
    """
    return df.memory_usage(deep=True).sum() / (1024 * 1024)


def check_memory_limit(df: pd.DataFrame, limit_mb: float = MEMORY_LIMIT_BYTES / (1024**2)) -> bool:
    """
    Check if a DataFrame's memory usage is within the specified limit.
    
    Args:
        df: The DataFrame to check.
        limit_mb: Memory limit in MB.
        
    Returns:
        True if within limit, False otherwise.
    """
    usage = estimate_memory_usage(df)
    if usage > limit_mb:
        logger.warning(
            f"DataFrame memory usage ({usage:.2f} MB) exceeds limit ({limit_mb:.2f} MB)"
        )
        return False
    return True
