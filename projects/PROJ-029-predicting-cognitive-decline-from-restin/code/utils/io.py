"""IO utilities for the project."""
from __future__ import annotations

import csv
import json
import os
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd


def ensure_dir(path: Union[str, Path]) -> Path:
    """Ensure directory exists."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_csv(file_path: Union[str, Path]) -> pd.DataFrame:
    """Load a CSV file into a DataFrame."""
    return pd.read_csv(file_path)


def save_csv(df: pd.DataFrame, file_path: Union[str, Path]) -> None:
    """Save a DataFrame to a CSV file."""
    ensure_dir(Path(file_path).parent)
    df.to_csv(file_path, index=False)


def load_json(file_path: Union[str, Path]) -> Any:
    """Load a JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)


def save_json(data: Any, file_path: Union[str, Path]) -> None:
    """Save data to a JSON file."""
    ensure_dir(Path(file_path).parent)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)


def load_pickle(file_path: Union[str, Path]) -> Any:
    """Load a pickle file."""
    with open(file_path, 'rb') as f:
        return pickle.load(f)


def save_pickle(obj: Any, file_path: Union[str, Path]) -> None:
    """Save an object to a pickle file."""
    ensure_dir(Path(file_path).parent)
    with open(file_path, 'wb') as f:
        pickle.dump(obj, f)


def save_text(text: str, file_path: Union[str, Path]) -> None:
    """Save text to a file."""
    ensure_dir(Path(file_path).parent)
    with open(file_path, 'w') as f:
        f.write(text)


def load_numpy(file_path: Union[str, Path]) -> np.ndarray:
    """Load a NumPy array."""
    return np.load(file_path)


def save_numpy(arr: np.ndarray, file_path: Union[str, Path]) -> None:
    """Save a NumPy array."""
    ensure_dir(Path(file_path).parent)
    np.save(file_path, arr)
