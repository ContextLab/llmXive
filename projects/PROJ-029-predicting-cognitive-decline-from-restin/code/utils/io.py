"""
Utility functions for I/O operations.
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


def ensure_dir(path: Union[str, Path]) -> Path:
    """Ensure a directory exists, creating it if necessary."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def load_csv(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """Load a CSV file and return a list of dictionaries."""
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)


def save_csv(data: List[Dict[str, Any]], file_path: Union[str, Path], fieldnames: Optional[List[str]] = None) -> None:
    """Save a list of dictionaries to a CSV file."""
    ensure_dir(Path(file_path).parent)
    if not data:
        # Write empty file or just header?
        # If no data, we can't infer fieldnames.
        # Assume empty list means no rows.
        pass
    
    if fieldnames is None and data:
        fieldnames = list(data[0].keys())
    
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)


def load_json(file_path: Union[str, Path]) -> Any:
    """Load a JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)


def save_json(data: Any, file_path: Union[str, Path]) -> None:
    """Save data to a JSON file."""
    ensure_dir(Path(file_path).parent)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)


def load_pickle(file_path: Union[str, Path]) -> Any:
    """Load a pickle file."""
    with open(file_path, 'rb') as f:
        return pickle.load(f)


def save_pickle(data: Any, file_path: Union[str, Path]) -> None:
    """Save data to a pickle file."""
    ensure_dir(Path(file_path).parent)
    with open(file_path, 'wb') as f:
        pickle.dump(obj, f)


def save_text(text: str, file_path: Union[str, Path]) -> None:
    """Save text to a file."""
    ensure_dir(Path(file_path).parent)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(text)


def load_numpy(file_path: Union[str, Path]) -> np.ndarray:
    """Load a NumPy array."""
    return np.load(file_path)


def save_numpy(data: np.ndarray, file_path: Union[str, Path]) -> None:
    """Save a numpy array to a file."""
    ensure_dir(Path(file_path).parent)
    np.save(file_path, data)
