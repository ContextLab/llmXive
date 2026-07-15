"""I/O utilities for the project."""
from __future__ import annotations

import csv
import json
import os
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np


def ensure_dir(path: Union[str, Path]) -> Path:
    """Create directory if it doesn't exist."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_csv(path: Union[str, Path]) -> List[Dict[str, str]]:
    """Load a CSV file into a list of dictionaries."""
    path = Path(path)
    with open(path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        return list(reader)


def save_csv(data: List[Dict[str, Any]], path: Union[str, Path]) -> None:
    """Save a list of dictionaries to a CSV file."""
    path = Path(path)
    ensure_dir(path.parent)
    if not data:
        with open(path, 'w', newline='') as f:
            f.write("")
        return
    
    fieldnames = list(data[0].keys())
    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def load_json(path: Union[str, Path]) -> Any:
    """Load a JSON file."""
    path = Path(path)
    with open(path, 'r') as f:
        return json.load(f)


def save_json(data: Any, path: Union[str, Path]) -> None:
    """Save data to a JSON file."""
    path = Path(path)
    ensure_dir(path.parent)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, default=str)


def load_pickle(path: Union[str, Path]) -> Any:
    """Load a pickle file."""
    path = Path(path)
    with open(path, 'rb') as f:
        return pickle.load(f)


def save_pickle(data: Any, path: Union[str, Path]) -> None:
    """Save data to a pickle file."""
    path = Path(path)
    ensure_dir(path.parent)
    with open(path, 'wb') as f:
        pickle.dump(data, f)


def save_text(text: str, path: Union[str, Path]) -> None:
    """Save text to a file."""
    path = Path(path)
    ensure_dir(path.parent)
    with open(path, 'w') as f:
        f.write(text)


def load_numpy(path: Union[str, Path]) -> np.ndarray:
    """Load a NumPy array from a .npy file."""
    path = Path(path)
    return np.load(path)


def save_numpy(array: np.ndarray, path: Union[str, Path]) -> None:
    """Save a NumPy array to a .npy file."""
    path = Path(path)
    ensure_dir(path.parent)
    np.save(path, array)