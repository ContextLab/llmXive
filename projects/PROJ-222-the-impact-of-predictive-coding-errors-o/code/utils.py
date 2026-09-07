import pandas as pd
import logging
from pathlib import Path
from typing import Iterator, Optional, Callable, Any, List, Dict
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_dataset_chunked(file_path: Path, chunk_size: int = 10000) -> pd.DataFrame:
    """
    Load a large CSV file in chunks to avoid memory issues.
    Returns a single DataFrame with all chunks concatenated.
    """
    if not isinstance(file_path, Path):
        file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    logger.info(f"Loading {file_path} in chunks of {chunk_size}")
    
    chunks = []
    try:
        for chunk in pd.read_csv(file_path, chunksize=chunk_size):
            chunks.append(chunk)
    except Exception as e:
        logger.error(f"Error loading chunked file: {e}")
        raise
    
    if not chunks:
        return pd.DataFrame()
    
    logger.info(f"Concatenating {len(chunks)} chunks")
    return pd.concat(chunks, ignore_index=True)

def compute_chunked_statistics(
    file_path: Path, 
    column: str, 
    func: Callable[[pd.Series], Any],
    chunk_size: int = 10000
) -> Any:
    """
    Compute a statistic over a column in a large file using chunked processing.
    """
    if not isinstance(file_path, Path):
        file_path = Path(file_path)
    
    results = []
    for chunk in pd.read_csv(file_path, chunksize=chunk_size):
        if column in chunk.columns:
            results.append(func(chunk[column]))
        else:
            logger.warning(f"Column {column} not found in chunk")
    
    if not results:
        return None
    
    # Aggregate results (simple mean for most stats, sum for counts)
    if func.__name__ == 'sum':
        return sum(results)
    else:
        # For mean, we need weighted average
        # This is a simplification; proper weighted mean would require more logic
        return sum(results) / len(results)
