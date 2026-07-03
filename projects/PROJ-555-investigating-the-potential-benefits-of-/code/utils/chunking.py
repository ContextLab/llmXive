"""
Memory-safe chunking utilities for large data processing.

This module provides utilities to process large datasets in chunks
to ensure peak RAM usage stays below 7GB.
"""

import gc
from typing import List, Any, Callable, Optional, Iterator
import pandas as pd

def process_chunked(
    df: pd.DataFrame,
    chunk_size: int,
    process_func: Callable[[pd.DataFrame], Any],
    progress: bool = True
) -> List[Any]:
    """
    Process a DataFrame in chunks to manage memory usage.
    
    Args:
        df: Input DataFrame
        chunk_size: Number of rows per chunk
        process_func: Function to apply to each chunk
        progress: Whether to show progress bar
        
    Returns:
        List of results from processing each chunk
    """
    results = []
    total_rows = len(df)
    num_chunks = (total_rows + chunk_size - 1) // chunk_size
    
    for i in range(0, total_rows, chunk_size):
        chunk = df.iloc[i:i+chunk_size]
        result = process_func(chunk)
        results.append(result)
        
        # Force garbage collection every 10 chunks
        if i > 0 and (i // chunk_size) % 10 == 0:
            gc.collect()
    
    return results

def split_dataframe(df: pd.DataFrame, chunk_size: int) -> Iterator[pd.DataFrame]:
    """
    Generator that yields chunks of a DataFrame.
    
    Args:
        df: Input DataFrame
        chunk_size: Number of rows per chunk
        
    Yields:
        DataFrames of size chunk_size (last chunk may be smaller)
    """
    for i in range(0, len(df), chunk_size):
        yield df.iloc[i:i+chunk_size]
