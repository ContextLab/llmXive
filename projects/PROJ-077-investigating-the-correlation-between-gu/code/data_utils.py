import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any, Iterator, Union
import os
import itertools
from config import SAMPLE_LIMIT
from logging_config import get_logger, log_warning

logger = get_logger("data_utils")

def load_csv_streaming(path: str, limit: int = SAMPLE_LIMIT) -> pd.DataFrame:
    """
    Load a CSV file in streaming mode, limiting the number of rows.
    
    Args:
        path: Path to the CSV file.
        limit: Maximum number of rows to load.
        
    Returns:
        pd.DataFrame: Loaded data (limited to `limit` rows).
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
        
    # Use chunked reading for large files
    chunks = []
    total_rows = 0
    
    for chunk in pd.read_csv(path, chunksize=10000):
        chunks.append(chunk)
        total_rows += len(chunk)
        if total_rows >= limit:
            break
            
    df = pd.concat(chunks, ignore_index=True)
    
    # Enforce limit strictly
    if len(df) > limit:
        df = df.iloc[:limit]
        log_warning(f"Stream contained more than {limit} rows. Truncated to {limit}.")
        
    return df

def load_chunked(path: str, chunk_size: int = 10000) -> Iterator[pd.DataFrame]:
    """
    Loads a CSV in chunks. Raises FileNotFoundError if path does not exist.
    Yields pandas DataFrames.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
        
    for chunk in pd.read_csv(path, chunksize=chunk_size):
        yield chunk
