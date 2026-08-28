"""
Utility functions for file I/O operations.
"""
from __future__ import annotations

import csv
import json
import os
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd

from utils.logger import get_logger

logger = get_logger("io_utils")

def ensure_dir(path: Union[str, Path]) -> Path:
    """Ensure a directory exists, creating it if necessary."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def load_csv(path: Union[str, Path], **kwargs) -> pd.DataFrame:
    """Load a CSV file into a pandas DataFrame."""
    path = Path(path)
    if not path.exists():
        logger.log("file_not_found", path=str(path), operation="load_csv")
        raise FileNotFoundError(f"File not found: {path}")
    return pd.read_csv(path, **kwargs)

def save_csv(df: pd.DataFrame, path: Union[str, Path], **kwargs) -> None:
    """Save a pandas DataFrame to a CSV file."""
    path = Path(path)
    ensure_dir(path.parent)
    df.to_csv(path, index=False, **kwargs)
    logger.log("file_saved", path=str(path), operation="save_csv")

def load_json(path: Union[str, Path], **kwargs) -> Any:
    """Load a JSON file."""
    path = Path(path)
    if not path.exists():
        logger.log("file_not_found", path=str(path), operation="load_json")
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f, **kwargs)

def save_json(data: Any, path: Union[str, Path], **kwargs) -> None:
    """Save data to a JSON file."""
    path = Path(path)
    ensure_dir(path.parent)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str, **kwargs)
    logger.log("file_saved", path=str(path), operation="save_json")

def load_pickle(path: Union[str, Path]) -> Any:
    """Load a pickle file."""
    path = Path(path)
    if not path.exists():
        logger.log("file_not_found", path=str(path), operation="load_pickle")
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, 'rb') as f:
        return pickle.load(f)

def save_pickle(data: Any, path: Union[str, Path]) -> None:
    """Save data to a pickle file."""
    path = Path(path)
    ensure_dir(path.parent)
    with open(path, 'wb') as f:
        pickle.dump(data, f)
    logger.log("file_saved", path=str(path), operation="save_pickle")

def save_text(text: str, path: Union[str, Path], encoding: str = 'utf-8') -> None:
    """Save text to a file."""
    path = Path(path)
    ensure_dir(path.parent)
    with open(path, 'w', encoding=encoding) as f:
        f.write(text)
    logger.log("file_saved", path=str(path), operation="save_text")

def load_numpy(path: Union[str, Path]) -> np.ndarray:
    """Load a NumPy .npy file."""
    path = Path(path)
    if not path.exists():
        logger.log("file_not_found", path=str(path), operation="load_numpy")
        raise FileNotFoundError(f"File not found: {path}")
    return np.load(path)

def save_numpy(arr: np.ndarray, path: Union[str, Path]) -> None:
    """Save a NumPy array to a .npy file."""
    path = Path(path)
    ensure_dir(path.parent)
    np.save(path, arr)
    logger.log("file_saved", path=str(path), operation="save_numpy")