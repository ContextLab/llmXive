"""
Data Utilities Module.
Helper functions for loading and validating data.
"""
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any, Iterator, Union
import os

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
