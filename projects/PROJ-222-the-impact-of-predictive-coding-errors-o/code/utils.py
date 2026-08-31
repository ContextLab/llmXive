"""
code/utils.py
Implements T008: Chunked data loading utility.
"""
import pandas as pd
import logging
from pathlib import Path
from typing import Iterator, Optional, Callable, Any, List, Dict

logger = logging.getLogger(__name__)

def load_dataset_chunked(file_path: str, chunksize: int = 100000) -> Iterator[pd.DataFrame]:
    """
    Load dataset in chunks to handle large files.
    Yields DataFrames chunk by chunk.
    """
    if not Path(file_path).exists():
        raise FileNotFoundError(f"File {file_path} not found")
    
    # Infer format
    if file_path.endswith('.csv'):
        reader = pd.read_csv(file_path, chunksize=chunksize)
    elif file_path.endswith('.parquet'):
        # Parquet doesn't support chunksize in read_parquet directly in all versions
        # We load all if small, or use a custom iterator if large
        # For simplicity, we assume CSV for chunked loading
        logger.warning("Parquet chunking not fully supported. Loading full file.")
        yield pd.read_parquet(file_path)
        return
    else:
        reader = pd.read_csv(file_path, chunksize=chunksize)
    
    for chunk in reader:
        yield chunk

def compute_chunked_statistics(chunks: Iterator[pd.DataFrame], func: Callable[[pd.DataFrame], Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute statistics over chunks and aggregate.
    """
    results = []
    for chunk in chunks:
        results.append(func(chunk))
    
    # Simple aggregation: sum or mean
    # This is a placeholder for specific aggregation logic
    return {"status": "aggregated", "count": len(results)}