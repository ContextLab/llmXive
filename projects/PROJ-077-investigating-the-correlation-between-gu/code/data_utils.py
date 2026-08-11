"""
Data Utilities Module.
Helper functions for loading and validating data with streaming support.
"""
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any, Iterator, Union
import os
import itertools
from config import SAMPLE_LIMIT

def load_csv_with_dtypes(file_path: str, chunksize: Optional[int] = None) -> Union[pd.DataFrame, Iterator[pd.DataFrame]]:
    """
    Loads a CSV file. If chunksize is provided, returns an iterator.
    Otherwise, loads the whole file.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if chunksize:
        return pd.read_csv(file_path, chunksize=chunksize)
    else:
        return pd.read_csv(file_path)

def get_chunk_paths(base_path: str, pattern: str = "*.csv") -> List[str]:
    """Returns a list of chunk file paths."""
    path = Path(base_path)
    return [str(f) for f in path.glob(pattern)]

def get_file_info(file_path: str) -> Dict[str, Any]:
    """Returns basic info about a file."""
    if not os.path.exists(file_path):
        return {}
    size = os.path.getsize(file_path)
    return {'path': file_path, 'size_bytes': size}

def validate_csv_structure(file_path: str, required_columns: List[str]) -> bool:
    """Checks if a CSV has required columns."""
    try:
        df = pd.read_csv(file_path, nrows=0)
        return all(col in df.columns for col in required_columns)
    except Exception:
        return False

def load_streaming_dataset(dataset_id: str, config_name: Optional[str] = None, limit: Optional[int] = None) -> Iterator[Dict[str, Any]]:
    """
    Loads a dataset from the Hugging Face datasets library in streaming mode.
    
    Args:
        dataset_id: The dataset identifier (e.g., 'ukbiobank/microbiome-cognitive').
        config_name: Optional configuration name.
        limit: Maximum number of rows to yield. If None, yields all available data.
    
    Yields:
        Dictionary rows from the dataset.
    
    Raises:
        ImportError: If 'datasets' library is not installed.
        FileNotFoundError: If the dataset cannot be found or accessed.
        RuntimeError: If streaming is not supported by the dataset.
    """
    try:
        from datasets import load_dataset
    except ImportError:
        raise ImportError("The 'datasets' library is required for streaming. Install it via 'pip install datasets'.")

    try:
        if config_name:
            ds = load_dataset(dataset_id, config_name, streaming=True)
        else:
            ds = load_dataset(dataset_id, streaming=True)
    except Exception as e:
        raise FileNotFoundError(f"Failed to load dataset '{dataset_id}' from remote source: {e}")

    # Determine the split to use (usually 'train' or 'default')
    # HuggingFace streaming datasets often have a 'train' split by default if not specified
    split_name = 'train' if 'train' in ds else list(ds.keys())[0]
    split_iter = ds[split_name]

    if limit is not None:
        split_iter = itertools.islice(split_iter, limit)
    
    return split_iter

def load_csv_streaming(file_path: str, limit: Optional[int] = None, chunksize: int = 1000) -> Iterator[pd.DataFrame]:
    """
    Loads a local CSV file in a streaming/chunked manner, enforcing a row limit.
    
    Args:
        file_path: Path to the local CSV file.
        limit: Maximum total rows to process across all chunks.
        chunksize: Number of rows to read per chunk.
    
    Yields:
        Pandas DataFrames containing chunks of data.
    
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Local file not found: {file_path}")

    if limit is None:
        limit = SAMPLE_LIMIT

    total_yielded = 0
    
    for chunk in pd.read_csv(file_path, chunksize=chunksize):
        if total_yielded >= limit:
            break
        
        remaining = limit - total_yielded
        if remaining < len(chunk):
            chunk = chunk.iloc[:remaining]
        
        total_yielded += len(chunk)
        yield chunk

        if total_yielded >= limit:
            break