"""
I/O utilities for loading and saving various data formats.
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


def ensure_dir(directory: Union[str, Path]) -> Path:
    """Ensure a directory exists, creating it if necessary."""
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_csv(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """Load a CSV file and return as a list of dictionaries."""
    with open(file_path, "r", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def save_csv(file_path: Union[str, Path], data: List[Dict[str, Any]], fieldnames: Optional[List[str]] = None) -> None:
    """Save a list of dictionaries to a CSV file."""
    file_path = Path(file_path)
    ensure_dir(file_path.parent)
    
    if not data:
        # Create empty file with headers if fieldnames provided
        with open(file_path, "w", newline="") as f:
            if fieldnames:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
        return
    
    if fieldnames is None:
        fieldnames = list(data[0].keys())
    
    with open(file_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def load_json(file_path: Union[str, Path]) -> Any:
    """Load a JSON file and return its contents."""
    with open(file_path, "r") as f:
        return json.load(f)


def save_json(file_path: Union[str, Path], data: Any, indent: int = 2) -> None:
    """Save data to a JSON file."""
    file_path = Path(file_path)
    ensure_dir(file_path.parent)
    
    with open(file_path, "w") as f:
        json.dump(data, f, indent=indent, default=str)


def load_pickle(file_path: Union[str, Path]) -> Any:
    """Load a pickle file and return its contents."""
    with open(file_path, "rb") as f:
        return pickle.load(f)


def save_pickle(file_path: Union[str, Path], data: Any) -> None:
    """Save data to a pickle file."""
    file_path = Path(file_path)
    ensure_dir(file_path.parent)
    
    with open(file_path, "wb") as f:
        pickle.dump(data, f)


def save_text(file_path: Union[str, Path], text: str) -> None:
    """Save text to a file."""
    file_path = Path(file_path)
    ensure_dir(file_path.parent)
    
    with open(file_path, "w") as f:
        f.write(text)


def load_numpy(file_path: Union[str, Path]) -> np.ndarray:
    """Load a NumPy .npy file."""
    return np.load(file_path)


def save_numpy(file_path: Union[str, Path], data: np.ndarray) -> None:
    """Save a NumPy array to a .npy file."""
    file_path = Path(file_path)
    ensure_dir(file_path.parent)
    np.save(file_path, data)
