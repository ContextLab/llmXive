"""
Streaming and batch data loader utilities for large datasets.

Designed to handle datasets >14GB within 7GB RAM limits by processing
data in batches/chunks and yielding results incrementally.
"""
import os
import gc
import logging
from pathlib import Path
from typing import (
    Generator,
    List,
    Optional,
    Union,
    Iterator,
    Dict,
    Any,
    Tuple,
)
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import numpy as np

from code.utils.logging import get_logger, DataLoadError

logger = get_logger(__name__)

# Default memory limit in bytes (7GB)
DEFAULT_MEMORY_LIMIT = 7 * 1024**3
# Default batch size for CSV reading
DEFAULT_CSV_CHUNK_SIZE = 100_000
# Default batch size for Parquet row groups
DEFAULT_PARQUET_ROW_GROUP_SIZE = 100_000


class StreamingLoader:
    """
    A streaming loader that reads large files in batches to stay within memory limits.
    
    Supports CSV and Parquet formats. For Parquet, it leverages PyArrow's row group
    streaming capabilities. For CSV, it uses pandas' chunksize parameter.
    
    Attributes:
        file_path: Path to the data file.
        file_format: Format of the file ('csv' or 'parquet').
        batch_size: Number of rows to read per batch (CSV) or row group target (Parquet).
        memory_limit: Maximum memory usage target in bytes.
    """
    
    def __init__(
        self,
        file_path: Union[str, Path],
        file_format: Optional[str] = None,
        batch_size: int = DEFAULT_CSV_CHUNK_SIZE,
        memory_limit: int = DEFAULT_MEMORY_LIMIT,
    ):
        self.file_path = Path(file_path)
        self.batch_size = batch_size
        self.memory_limit = memory_limit
        
        if file_format is None:
            self.file_format = self.file_path.suffix.lstrip('.').lower()
            if self.file_format not in ('csv', 'parquet'):
                raise ValueError(f"Unsupported file format: {self.file_format}. Must be 'csv' or 'parquet'.")
        else:
            self.file_format = file_format.lower()
            if self.file_format not in ('csv', 'parquet'):
                raise ValueError(f"Unsupported file format: {file_format}. Must be 'csv' or 'parquet'.")

        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")

        logger.info(f"Initialized StreamingLoader for {self.file_path} ({self.file_format})")

    def __iter__(self) -> Iterator[pd.DataFrame]:
        """
        Iterate over the file in batches, yielding DataFrames.
        
        Yields:
            pd.DataFrame: A batch of rows from the file.
        
        Raises:
            DataLoadError: If reading fails or memory limits are exceeded.
        """
        if self.file_format == 'csv':
            yield from self._stream_csv()
        elif self.file_format == 'parquet':
            yield from self._stream_parquet()
        else:
            raise ValueError(f"Unsupported format: {self.file_format}")

    def _stream_csv(self) -> Generator[pd.DataFrame, None, None]:
        """Stream a CSV file in chunks."""
        try:
            # Use chunksize to read in batches
            for chunk in pd.read_csv(
                self.file_path,
                chunksize=self.batch_size,
                low_memory=False,  # Prevent mixed type inference issues
            ):
                # Check memory usage before yielding
                mem_usage = estimate_memory_usage([chunk])
                if mem_usage > self.memory_limit:
                    logger.warning(
                        f"Batch size {self.batch_size} exceeds memory limit. "
                        f"Estimated usage: {mem_usage / 1e9:.2f}GB. "
                        f"Consider reducing batch_size."
                    )
                    # Force garbage collection before raising
                    gc.collect()
                
                yield chunk
                # Explicitly delete chunk reference if not needed, 
                # but generator handles scope. Force GC if memory is tight.
                if mem_usage > self.memory_limit * 0.9:
                    gc.collect()

        except Exception as e:
            raise DataLoadError(f"Failed to stream CSV file {self.file_path}: {e}") from e

    def _stream_parquet(self) -> Generator[pd.DataFrame, None, None]:
        """Stream a Parquet file by row groups."""
        try:
            parquet_file = pq.ParquetFile(self.file_path)
            logger.info(f"Parquet file has {parquet_file.metadata.num_row_groups} row groups")

            for i, row_group in enumerate(parquet_file.iter_batches(batch_size=self.batch_size)):
                # Convert PyArrow Table to Pandas DataFrame
                df = row_group.to_pandas()
                
                mem_usage = estimate_memory_usage([df])
                if mem_usage > self.memory_limit:
                    logger.warning(
                        f"Row group {i} exceeds memory limit. "
                        f"Estimated usage: {mem_usage / 1e9:.2f}GB."
                    )
                    gc.collect()
                
                yield df

                if mem_usage > self.memory_limit * 0.9:
                    gc.collect()

        except Exception as e:
            raise DataLoadError(f"Failed to stream Parquet file {self.file_path}: {e}") from e


def load_in_batches(
    file_path: Union[str, Path],
    batch_size: int = DEFAULT_CSV_CHUNK_SIZE,
    file_format: Optional[str] = None,
    memory_limit: int = DEFAULT_MEMORY_LIMIT,
) -> Iterator[pd.DataFrame]:
    """
    Convenience function to load a file in batches.
    
    Args:
        file_path: Path to the file.
        batch_size: Number of rows per batch.
        file_format: Optional format override.
        memory_limit: Maximum memory usage in bytes.
        
    Yields:
        pd.DataFrame: Batches of data.
    """
    loader = StreamingLoader(
        file_path=file_path,
        file_format=file_format,
        batch_size=batch_size,
        memory_limit=memory_limit,
    )
    return iter(loader)


def concatenate_batches(
    batches: List[pd.DataFrame],
    memory_limit: int = DEFAULT_MEMORY_LIMIT,
) -> pd.DataFrame:
    """
    Concatenate a list of batches into a single DataFrame.
    
    Performs checks to ensure the operation won't exceed memory limits.
    
    Args:
        batches: List of DataFrames to concatenate.
        memory_limit: Maximum allowed memory usage in bytes.
        
    Returns:
        pd.DataFrame: Concatenated DataFrame.
        
    Raises:
        DataLoadError: If concatenation would exceed memory limits.
    """
    if not batches:
        return pd.DataFrame()
    
    # Estimate memory usage of result
    # Approximate: sum of individual sizes + overhead
    total_size = sum(estimate_memory_usage([df]) for df in batches)
    
    if total_size > memory_limit:
        raise DataLoadError(
            f"Concatenating {len(batches)} batches would exceed memory limit. "
            f"Estimated total size: {total_size / 1e9:.2f}GB > {memory_limit / 1e9:.2f}GB"
        )
    
    try:
        result = pd.concat(batches, ignore_index=True)
        return result
    except Exception as e:
        raise DataLoadError(f"Failed to concatenate batches: {e}") from e


def estimate_memory_usage(dfs: List[pd.DataFrame]) -> float:
    """
    Estimate the memory usage of a list of DataFrames in bytes.
    
    Uses pandas' memory_usage method with deep=True for accuracy.
    
    Args:
        dfs: List of DataFrames to estimate.
        
    Returns:
        float: Total estimated memory usage in bytes.
    """
    total_bytes = 0.0
    for df in dfs:
        if df is not None:
            # memory_usage returns a Series for each column, sum() gives total
            # deep=True ensures object dtypes are fully measured
            total_bytes += df.memory_usage(deep=True).sum()
    return float(total_bytes)


def get_file_size(file_path: Union[str, Path]) -> int:
    """
    Get the size of a file in bytes.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        int: File size in bytes.
    """
    return os.path.getsize(file_path)


def process_with_streaming(
    file_path: Union[str, Path],
    processor_func: callable,
    batch_size: int = DEFAULT_CSV_CHUNK_SIZE,
    memory_limit: int = DEFAULT_MEMORY_LIMIT,
    output_file: Optional[Union[str, Path]] = None,
) -> Optional[pd.DataFrame]:
    """
    Process a large file in streaming batches without loading it all into memory.
    
    This function applies a processor function to each batch and optionally
    aggregates results or writes to an output file.
    
    Args:
        file_path: Path to the input file.
        processor_func: Function that takes a DataFrame and returns processed data.
                        Signature: (df: pd.DataFrame) -> pd.DataFrame
        batch_size: Number of rows per batch.
        memory_limit: Maximum memory usage in bytes.
        output_file: Optional path to write aggregated results.
        
    Returns:
        Optional[pd.DataFrame]: Aggregated results if output_file is not specified.
                                None if results are written to file.
        
    Raises:
        DataLoadError: If processing fails.
    """
    results = []
    
    try:
        for i, batch in enumerate(load_in_batches(file_path, batch_size, memory_limit=memory_limit)):
            logger.debug(f"Processing batch {i} with {len(batch)} rows")
            
            processed_batch = processor_func(batch)
            
            if processed_batch is not None and not processed_batch.empty:
                results.append(processed_batch)
                
                # Periodic memory cleanup
                if i % 10 == 0:
                    gc.collect()
                    
                    # Check if accumulated results are getting too large
                    if output_file is None and estimate_memory_usage(results) > memory_limit * 0.8:
                        logger.warning(
                            "Accumulated results approaching memory limit. "
                            "Consider writing intermediate results to disk or using a smaller batch."
                        )

        if output_file:
            if results:
                final_df = concatenate_batches(results, memory_limit=memory_limit)
                # Infer format from extension
                output_path = Path(output_file)
                if output_path.suffix == '.parquet':
                    final_df.to_parquet(output_path, index=False)
                elif output_path.suffix == '.csv':
                    final_df.to_csv(output_path, index=False)
                else:
                    raise ValueError(f"Unsupported output format: {output_path.suffix}")
                logger.info(f"Wrote processed results to {output_file}")
                return None
            else:
                logger.warning("No results to write to output file")
                return None
        else:
            if results:
                return concatenate_batches(results, memory_limit=memory_limit)
            else:
                return pd.DataFrame()
                
    except Exception as e:
        raise DataLoadError(f"Failed to process file {file_path} with streaming: {e}") from e
    finally:
        # Ensure garbage collection after processing
        gc.collect()