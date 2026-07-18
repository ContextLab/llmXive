"""
I/O Utilities for llmXive.
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Union

import pandas as pd

def ensure_dir(path: Union[str, Path]) -> Path:
    """Creates a directory if it doesn't exist."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def compute_checksum(file_path: Union[str, Path], algorithm: str = "md5") -> str:
    """Computes the checksum of a file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found for checksum: {path}")
    
    hash_func = hashlib.new(algorithm)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def save_json(data: Any, path: Union[str, Path], indent: int = 2) -> None:
    """Saves data to a JSON file."""
    path = Path(path)
    ensure_dir(path.parent)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent)

def load_json(path: Union[str, Path]) -> Any:
    """Loads data from a JSON file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_csv(df: pd.DataFrame, path: Union[str, Path], index: bool = False) -> None:
    """Saves a DataFrame to a CSV file."""
    path = Path(path)
    ensure_dir(path.parent)
    df.to_csv(path, index=index)

def load_csv(path: Union[str, Path]) -> pd.DataFrame:
    """Loads a DataFrame from a CSV file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")
    return pd.read_csv(path)
