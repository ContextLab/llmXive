"""
Streaming and batch data loader utilities for large datasets.

Designed to handle >14GB datasets within a 7GB RAM limit by processing
data in chunks/batches without loading the entire file into memory.
"""
import os
import gc
from pathlib import Path
from typing import (
    Iterator,
    List,
    Optional,
    Union,
    Callable,
    Dict,
    Any,
    TextIO,
)

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import numpy as np

from utils.logging import get_logger, DataLoadError

logger = get_logger(__name__)

# Default memory limit in bytes (approx 6GB to stay safely under 7GB)
DEFAULT_MEMORY_LIMIT = 6 * 1024**3

# Default batch size for row-based processing
DEFAULT_BATCH_SIZE = 100_000

# Default chunk size for parquet reading (rows)
DEFAULT_PARQUET_ROW_GROUP_READ_SIZE = 1_000_000


class StreamingLoader:
    """
    A streaming loader for large CSV and Parquet files.
    
    This class provides an iterator interface to read large files in batches,
    ensuring memory usage stays within configured limits.
    """
    
    def __init__(
        self,
        file_path: Union[str, Path],
        memory_limit: int = DEFAULT_MEMORY_LIMIT,
        batch_size: int = DEFAULT_BATCH_SIZE,
        chunksize: Optional[int] = None,
        **read_kwargs: Any
    ):
        """
        Initialize the streaming loader.
        
        Args:
            file_path: Path to the input file (CSV or Parquet).
            memory_limit: Maximum memory usage in bytes before forcing a batch yield.
            batch_size: Target number of rows per batch (for CSV).
            chunksize: Explicit chunk size for parquet row groups (overrides default).
            **read_kwargs: Additional arguments passed to pandas/pandas-parquet readers.
        
        Raises:
            DataLoadError: If the file does not exist or format is unsupported.
        """
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise DataLoadError(f"File not found: {self.file_path}")
        
        self.memory_limit = memory_limit
        self.batch_size = batch_size
        self.chunksize = chunksize or DEFAULT_PARQUET_ROW_GROUP_READ_SIZE
        self.read_kwargs = read_kwargs
        
        # Infer format
        suffix = self.file_path.suffix.lower()
        if suffix == '.csv':
            self.format = 'csv'
        elif suffix in ('.parquet', '.pq'):
            self.format = 'parquet'
        else:
            raise DataLoadError(f"Unsupported file format: {suffix}")
        
        logger.info(f"Initialized StreamingLoader for {self.format} file: {self.file_path}")
    
    def __iter__(self) -> Iterator[pd.DataFrame]:
        """
        Iterate over the file in batches.
        
        Yields:
            pd.DataFrame: A batch of rows from the file.
        """
        if self.format == 'csv':
            yield from self._stream_csv()
        elif self.format == 'parquet':
            yield from self._stream_parquet()
        else:
            raise DataLoadError(f"Unknown format: {self.format}")
    
    def _stream_csv(self) -> Iterator[pd.DataFrame]:
        """Stream a CSV file in batches."""
        # Use pandas chunksize for memory-efficient iteration
        chunksize = self.read_kwargs.pop('chunksize', self.batch_size)
        
        try:
            for chunk in pd.read_csv(self.file_path, chunksize=chunksize, **self.read_kwargs):
                yield chunk
                # Force garbage collection occasionally if memory is tight
                # (Heuristic: check if we've yielded a few batches)
        except Exception as e:
            raise DataLoadError(f"Error reading CSV file {self.file_path}: {e}")
    
    def _stream_parquet(self) -> Iterator[pd.DataFrame]:
        """Stream a Parquet file in batches using PyArrow."""
        try:
            parquet_file = pq.ParquetFile(self.file_path)
            row_groups = parquet_file.metadata.num_row_groups
            
            # If chunksize is smaller than row group size, we might need to split,
            # but for simplicity we iterate row groups first.
            # To strictly adhere to memory limits, we could read row groups into memory
            # and split them, but standard PyArrow iteration is usually efficient enough.
            
            for i in range(row_groups):
                # Read a single row group (or multiple if chunksize allows)
                # Note: PyArrow read_row_group reads the whole group into memory.
                # If a single group is > memory_limit, this will fail.
                # For very large single groups, we would need to use fragments.
                
                table = parquet_file.read_row_group(i)
                
                # Convert to pandas
                df = table.to_pandas()
                
                # If the resulting DataFrame is larger than limit, split it?
                # Usually row groups are manageable, but let's enforce a hard split if needed.
                if self._estimate_memory_usage(df) > self.memory_limit:
                    # Split the large DataFrame into chunks
                    for start in range(0, len(df), self.batch_size):
                        yield df.iloc[start:start + self.batch_size]
                else:
                    yield df
                    
        except Exception as e:
            raise DataLoadError(f"Error reading Parquet file {self.file_path}: {e}")
    
    def _estimate_memory_usage(self, df: pd.DataFrame) -> int:
        """Estimate memory usage of a DataFrame in bytes."""
        return df.memory_usage(deep=True).sum()

def load_in_batches(
    file_path: Union[str, Path],
    callback: Callable[[pd.DataFrame, int], None],
    memory_limit: int = DEFAULT_MEMORY_LIMIT,
    batch_size: int = DEFAULT_BATCH_SIZE,
    **read_kwargs: Any
) -> None:
    """
    Process a file in batches, invoking a callback for each batch.
    
    Args:
        file_path: Path to the input file.
        callback: Function(batch_df, batch_index) to process each batch.
        memory_limit: Max memory limit in bytes.
        batch_size: Target rows per batch.
        **read_kwargs: Arguments for the loader.
    """
    loader = StreamingLoader(
        file_path=file_path,
        memory_limit=memory_limit,
        batch_size=batch_size,
        **read_kwargs
    )
    
    batch_idx = 0
    total_rows = 0
    
    for batch in loader:
        callback(batch, batch_idx)
        total_rows += len(batch)
        batch_idx += 1
        
        # Log progress periodically
        if batch_idx % 10 == 0:
            logger.debug(f"Processed {batch_idx} batches, {total_rows} rows total")
    
    logger.info(f"Completed loading {total_rows} rows from {file_path} in {batch_idx} batches")

def concatenate_batches(
    iterator: Iterator[pd.DataFrame],
    max_batches: Optional[int] = None,
    memory_limit: int = DEFAULT_MEMORY_LIMIT
) -> pd.DataFrame:
    """
    Concatenate batches from an iterator into a single DataFrame.
    
    WARNING: This loads data into memory. Use with caution if the total
    size exceeds available RAM. It enforces a memory limit check before
    concatenating each new batch.
    
    Args:
        iterator: Iterator yielding DataFrames.
        max_batches: Maximum number of batches to concatenate (None for all).
        memory_limit: Max memory allowed for the result.
        
    Returns:
        pd.DataFrame: Concatenated result.
        
    Raises:
        DataLoadError: If concatenation would exceed memory limits.
    """
    result_chunks = []
    current_size = 0
    batches_processed = 0
    
    for batch in iterator:
        if max_batches is not None and batches_processed >= max_batches:
            break
        
        batch_size = batch.memory_usage(deep=True).sum()
        
        if current_size + batch_size > memory_limit:
            raise DataLoadError(
                f"Concatenating next batch would exceed memory limit. "
                f"Current: {current_size / 1e9:.2f}GB, Batch: {batch_size / 1e9:.2f}GB, "
                f"Limit: {memory_limit / 1e9:.2f}GB"
            )
        
        result_chunks.append(batch)
        current_size += batch_size
        batches_processed += 1
    
    if not result_chunks:
        return pd.DataFrame()
    
    logger.info(f"Concatenating {batches_processed} batches ({current_size / 1e9:.2f}GB)")
    return pd.concat(result_chunks, ignore_index=True)

def estimate_memory_usage(df: pd.DataFrame) -> int:
    """
    Estimate the memory usage of a DataFrame in bytes.
    
    Args:
        df: The DataFrame to estimate.
        
    Returns:
        int: Estimated memory usage in bytes.
    """
    return df.memory_usage(deep=True).sum()

def get_file_size(file_path: Union[str, Path]) -> int:
    """
    Get the size of a file in bytes.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        int: File size in bytes.
    """
    return Path(file_path).stat().st_size