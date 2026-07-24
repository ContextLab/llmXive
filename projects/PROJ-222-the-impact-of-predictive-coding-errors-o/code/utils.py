"""
Utility functions for data processing, specifically chunked loading
to handle large datasets within RAM constraints.
"""
import pandas as pd
import logging
from pathlib import Path
from typing import Iterator, Optional, Callable, Any, List, Dict

logger = logging.getLogger(__name__)

def load_dataset_chunked(
    file_path: str,
    chunksize: int = 100000,
    columns: Optional[List[str]] = None,
    dtype: Optional[Dict[str, Any]] = None,
    callback: Optional[Callable[[pd.DataFrame, int], pd.DataFrame]] = None
) -> Iterator[pd.DataFrame]:
    """
    Load a CSV dataset in chunks to manage memory usage for files >500MB.
    
    This generator yields DataFrames of the specified chunk size, allowing
    for streaming processing (e.g., computing statistics, filtering, or
    aggregation) without loading the entire file into RAM.
    
    Args:
        file_path: Path to the CSV file.
        chunksize: Number of rows per chunk. Default 100k.
        columns: List of columns to load. If None, loads all.
        dtype: Dictionary of column types to enforce.
        callback: Optional function applied to each chunk before yielding.
                 Signature: (chunk_df, chunk_index) -> processed_df.
                 
    Yields:
        pd.DataFrame: A chunk of the dataset.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file format is unsupported.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {file_path}")
    
    if path.suffix.lower() != '.csv':
        # For now, only CSV is supported for chunked loading in this utility.
        # Other formats (parquet) might need different handling or libraries.
        raise ValueError(f"Unsupported file format for chunked loading: {path.suffix}. Only .csv supported.")
    
    logger.info(f"Starting chunked load of {file_path} with chunksize={chunksize}")
    
    try:
        chunk_iter = pd.read_csv(
            file_path,
            chunksize=chunksize,
            usecols=columns,
            dtype=dtype,
            low_memory=False
        )
        
        chunk_idx = 0
        for chunk in chunk_iter:
            if callback:
                chunk = callback(chunk, chunk_idx)
            
            yield chunk
            chunk_idx += 1
            
            # Log progress every 10 chunks
            if chunk_idx % 10 == 0:
                logger.debug(f"Processed {chunk_idx} chunks ({chunk_idx * chunksize} rows)")
                
    except Exception as e:
        logger.error(f"Error during chunked loading: {e}")
        raise

def compute_chunked_statistics(
    file_path: str,
    columns: List[str],
    aggregations: Dict[str, List[str]]
) -> Dict[str, Any]:
    """
    Compute aggregate statistics over a large CSV file in chunks.
    
    This function iterates through the file in chunks, computing the
    requested aggregations (e.g., mean, sum, count) for specified columns,
    and combines the results at the end.
    
    Args:
        file_path: Path to the CSV file.
        columns: List of column names to aggregate.
        aggregations: Dict mapping column name to list of agg functions (e.g., {'duration': ['mean', 'sum']}).
        
    Returns:
        Dict containing the final aggregated results.
    """
    # Initialize results container
    results = {col: {} for col in columns}
    
    def process_chunk(chunk: pd.DataFrame, idx: int) -> pd.DataFrame:
        # Filter out rows with NaN in required columns for accurate stats
        valid_chunk = chunk[columns].dropna()
        
        if idx == 0:
            # Initialize accumulators if needed, but we'll compute on the fly
            # For simple aggregations like mean, we need sum and count
            pass
        
        return valid_chunk

    # We need a more robust way to aggregate means across chunks.
    # Strategy: Compute sum and count for each column, then derive mean at the end.
    # This function is a wrapper that calls load_dataset_chunked and accumulates state.
    
    # Re-initialize accumulators
    sum_accum = {col: 0.0 for col in columns}
    count_accum = {col: 0 for col in columns}
    
    # Handle the aggregations requested
    # We will compute 'count', 'sum', and 'mean' for all requested columns.
    # If other stats (like std) are needed, a more complex accumulation is required.
    
    logger.info(f"Computing statistics for {columns} on {file_path}")
    
    chunk_count = 0
    for chunk in load_dataset_chunked(file_path, columns=columns):
        chunk_count += 1
        for col in columns:
            if col in chunk.columns:
                non_null = chunk[col].dropna()
                sum_accum[col] += non_null.sum()
                count_accum[col] += len(non_null)
    
    # Finalize results
    final_results = {}
    for col in columns:
        final_results[col] = {
            'count': count_accum[col],
            'sum': sum_accum[col]
        }
        if count_accum[col] > 0:
            final_results[col]['mean'] = sum_accum[col] / count_accum[col]
        else:
            final_results[col]['mean'] = None
    
    logger.info(f"Processed {chunk_count} chunks. Statistics computed.")
    return final_results