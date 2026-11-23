"""
Optimized streaming data loader for large datasets.

This module provides an optimized streaming loader that processes data in chunks
while maintaining memory usage below 7GB constraints. It integrates with the
performance monitoring utilities to ensure safe processing of large datasets.
"""

import os
import gc
import logging
from pathlib import Path
from typing import (
    Optional, Dict, Any, List, Tuple, Iterator, Union, Callable
)

import pandas as pd
import numpy as np

from code.perf_monitor import (
    get_current_memory_usage,
    estimate_dataframe_memory,
    calculate_safe_batch_size,
    trigger_memory_cleanup,
    check_memory_pressure,
    stream_with_memory_monitor,
    optimize_dataframe_memory,
    validate_memory_constraints
)
from code.utils.streaming import StreamingLoader

logger = logging.getLogger(__name__)

class OptimizedStreamingLoader:
    """
    Optimized streaming loader with memory-aware batch processing.
    """
    
    def __init__(
        self,
        file_path: str,
        batch_size: Optional[int] = None,
        columns: Optional[List[str]] = None,
        memory_limit_gb: float = 6.0,
        chunksize: int = 100000
    ):
        """
        Initialize the optimized streaming loader.
        
        Args:
            file_path: Path to the data file.
            batch_size: Number of rows per batch (auto-calculated if None).
            columns: Optional list of columns to load.
            memory_limit_gb: Memory limit in GB (default 6.0).
            chunksize: Initial chunk size for reading.
        """
        self.file_path = Path(file_path)
        self.columns = columns
        self.memory_limit_gb = memory_limit_gb
        self.chunksize = chunksize
        
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Auto-calculate batch size if not provided
        if batch_size is None:
            # Create a small sample to estimate
            try:
                sample_df = pd.read_parquet(
                    self.file_path,
                    columns=columns[:5] if columns else None,
                    nrows=1000
                ) if self.file_path.suffix == '.parquet' else None
                
                if sample_df is not None:
                    self.batch_size = calculate_safe_batch_size(
                        df_sample=sample_df,
                        num_columns_hint=len(columns) if columns else 10
                    )
                else:
                    self.batch_size = 10000
            except Exception as e:
                logger.warning(f"Could not estimate batch size: {e}. Using default.")
                self.batch_size = 10000
        else:
            self.batch_size = batch_size
        
        logger.info(f"Initialized OptimizedStreamingLoader with batch_size={self.batch_size:,}")
    
    def __iter__(self) -> Iterator[pd.DataFrame]:
        """
        Iterate over the dataset in batches.
        
        Yields:
            DataFrames containing batches of data.
        """
        if self.file_path.suffix == '.parquet':
            yield from self._stream_parquet()
        elif self.file_path.suffix in ['.csv', '.tsv']:
            yield from self._stream_csv()
        else:
            raise ValueError(f"Unsupported file format: {self.file_path.suffix}")
    
    def _stream_parquet(self) -> Iterator[pd.DataFrame]:
        """
        Stream data from a Parquet file in batches.
        """
        try:
            # Use pandas read_parquet with row groups if available
            # For large files, we'll read in chunks
            total_rows = 0
            
            # Try to read in batches using pyarrow if available
            try:
                import pyarrow.parquet as pq
                
                parquet_file = pq.ParquetFile(self.file_path)
                
                for batch in parquet_file.iter_batches(batch_size=self.batch_size):
                    df = batch.to_pandas()
                    
                    if self.columns:
                        df = df[self.columns]
                    
                    # Optimize memory
                    df = optimize_dataframe_memory(df)
                    
                    total_rows += len(df)
                    yield df
                    
                    # Monitor memory
                    if total_rows % (self.batch_size * 10) == 0:
                        is_pressure, _ = check_memory_pressure(threshold_percent=75.0)
                        if is_pressure:
                            trigger_memory_cleanup()
            
            except ImportError:
                # Fallback to pandas if pyarrow not available
                logger.warning("pyarrow not available, using pandas fallback")
                for chunk in pd.read_parquet(
                    self.file_path,
                    columns=self.columns,
                    engine='pyarrow' if 'pyarrow' in str(pd.__version__) else 'fastparquet'
                ):
                    df = optimize_dataframe_memory(chunk)
                    total_rows += len(df)
                    yield df
                    
        except Exception as e:
            logger.error(f"Error streaming parquet file: {e}")
            raise
    
    def _stream_csv(self) -> Iterator[pd.DataFrame]:
        """
        Stream data from a CSV file in batches.
        """
        try:
            for chunk in pd.read_csv(
                self.file_path,
                chunksize=self.chunksize,
                usecols=self.columns,
                low_memory=False
            ):
                # Optimize memory
                df = optimize_dataframe_memory(chunk)
                
                yield df
                
                # Monitor memory
                is_pressure, _ = check_memory_pressure(threshold_percent=75.0)
                if is_pressure:
                    trigger_memory_cleanup()
                    
        except Exception as e:
            logger.error(f"Error streaming CSV file: {e}")
            raise

def process_large_dataset_streaming(
    file_path: str,
    process_fn: Callable[[pd.DataFrame], pd.DataFrame],
    columns: Optional[List[str]] = None,
    batch_size: Optional[int] = None,
    cleanup_interval: int = 5
) -> Iterator[pd.DataFrame]:
    """
    Process a large dataset using optimized streaming with memory monitoring.
    
    Args:
        file_path: Path to the data file.
        process_fn: Function to apply to each batch.
        columns: Optional list of columns to load.
        batch_size: Number of rows per batch.
        cleanup_interval: Number of batches between cleanup cycles.
        
    Yields:
        Processed batches.
    """
    loader = OptimizedStreamingLoader(
        file_path=file_path,
        batch_size=batch_size,
        columns=columns
    )
    
    # Use the memory monitoring wrapper
    yield from stream_with_memory_monitor(
        loader=loader,
        process_fn=process_fn,
        batch_size_hint=batch_size,
        cleanup_interval=cleanup_interval
    )

def main():
    """
    Main function to demonstrate optimized streaming loader.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Testing optimized streaming loader")
    
    # Example usage (commented out to avoid requiring actual files)
    # loader = OptimizedStreamingLoader("data/raw/sample.parquet")
    # for batch in loader:
    #     logger.info(f"Processed batch with {len(batch)} rows")
    #     # Process batch...
    
    logger.info("Optimized streaming loader demonstration complete")

if __name__ == "__main__":
    main()
