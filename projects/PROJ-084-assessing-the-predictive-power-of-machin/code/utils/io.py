import os
import hashlib
import logging
from pathlib import Path
from typing import Optional, Union, List, Iterator, Dict, Any, Callable, TypeVar
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

logger = logging.getLogger(__name__)

def get_file_size_mb(file_path: Union[str, Path]) -> float:
    """Get file size in MB."""
    return os.path.getsize(file_path) / (1024 * 1024)

def calculate_md5(file_path: Union[str, Path]) -> str:
    """Calculate MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def verify_checksum(file_path: Union[str, Path], expected_md5: str) -> bool:
    """Verify file checksum against expected MD5."""
    actual_md5 = calculate_md5(file_path)
    return actual_md5 == expected_md5

def check_memory_limit(size_gb: float, limit_gb: float = 7.0) -> bool:
    """Check if estimated size is within memory limit."""
    return size_gb <= limit_gb

def load_parquet(file_path: Union[str, Path], chunksize: Optional[int] = None) -> Union[pd.DataFrame, Iterator[pd.DataFrame]]:
    """
    Load a Parquet file.
    If chunksize is provided, returns an iterator of DataFrames to manage memory.
    Otherwise, loads the whole file into a single DataFrame.
    """
    try:
        if chunksize:
            return pq.ParquetFile(file_path).iter_batches(batch_size=chunksize)
        else:
            return pd.read_parquet(file_path)
    except Exception as e:
        logger.error(f"Failed to load parquet file {file_path}: {e}")
        raise

def load_csv(file_path: Union[str, Path], chunksize: Optional[int] = None) -> Union[pd.DataFrame, Iterator[pd.DataFrame]]:
    """
    Load a CSV file.
    If chunksize is provided, returns an iterator of DataFrames.
    """
    try:
        if chunksize:
            return pd.read_csv(file_path, chunksize=chunksize)
        else:
            return pd.read_csv(file_path)
    except Exception as e:
        logger.error(f"Failed to load csv file {file_path}: {e}")
        raise

def save_parquet(df: pd.DataFrame, file_path: Union[str, Path], compression: str = 'snappy') -> None:
    """Save a DataFrame to Parquet."""
    df.to_parquet(file_path, compression=compression, index=False)

def save_csv(df: pd.DataFrame, file_path: Union[str, Path]) -> None:
    """Save a DataFrame to CSV."""
    df.to_csv(file_path, index=False)

def process_in_batches(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    process_func: Callable[[pd.DataFrame], pd.DataFrame],
    batch_size: int = 10000
) -> None:
    """
    Process a large file in batches to manage memory.
    Reads in chunks, applies process_func, and writes to output.
    Note: This assumes the output format is also Parquet and handles appending.
    For simplicity, we write to a temp file and merge, or overwrite if single batch logic is used.
    Here we assume we are processing and saving to a new file.
    """
    # Simple implementation: read all if fits, else warn.
    # For true streaming, we would need to manage the writer state.
    # Given the constraint, we try to read in chunks and write to a list, then concat.
    # If memory is tight, we should stream write.
    
    # Streaming write implementation:
    writer = None
    try:
        for batch in load_parquet(input_path, chunksize=batch_size):
            processed_batch = process_func(batch)
            if writer is None:
                # Initialize writer with schema from first batch
                writer = pq.ParquetWriter(output_path, processed_batch.schema)
            writer.write_batch(pa.Table.from_pandas(processed_batch))
    finally:
        if writer:
            writer.close()

def validate_memory_requirements(df: pd.DataFrame) -> float:
    """Estimate memory usage of a DataFrame in GB."""
    return df.memory_usage(deep=True).sum() / (1024 ** 3)
