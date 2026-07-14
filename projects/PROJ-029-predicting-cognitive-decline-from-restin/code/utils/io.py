"""I/O utilities for data loading and saving."""
from __future__ import annotations

import csv
import json
import os
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np


def ensure_dir(path: Union[str, Path]) -> Path:
    """Ensure a directory exists."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_csv(file_path: Union[str, Path], delimiter: str = ',') -> List[Dict[str, str]]:
    """Load a CSV file and return a list of dictionaries."""
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        return list(reader)


def save_csv(data: List[Dict[str, Any]], file_path: Union[str, Path], delimiter: str = ',') -> None:
    """Save a list of dictionaries to a CSV file."""
    file_path = Path(file_path)
    ensure_dir(file_path.parent)
    if not data:
        # Write empty file
        file_path.write_text("")
        return

    fieldnames = list(data[0].keys())
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
        writer.writeheader()
        writer.writerows(data)


def load_json(file_path: Union[str, Path]) -> Any:
    """Load a JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data: Any, file_path: Union[str, Path]) -> None:
    """Save data to a JSON file."""
    file_path = Path(file_path)
    ensure_dir(file_path.parent)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)


def load_pickle(file_path: Union[str, Path]) -> Any:
    """Load a pickle file."""
    with open(file_path, 'rb') as f:
        return pickle.load(f)


def save_pickle(data: Any, file_path: Union[str, Path]) -> None:
    """Save data to a pickle file."""
    file_path = Path(file_path)
    ensure_dir(file_path.parent)
    with open(file_path, 'wb') as f:
        pickle.dump(data, f)


def save_text(text: str, file_path: Union[str, Path]) -> None:
    """Save text to a file."""
    file_path = Path(file_path)
    ensure_dir(file_path.parent)
    file_path.write_text(text, encoding='utf-8')


def load_numpy(file_path: Union[str, Path]) -> np.ndarray:
    """Load a numpy file."""
    return np.load(file_path)


def save_numpy(data: np.ndarray, file_path: Union[str, Path]) -> None:
    """Save a numpy array to a file."""
    file_path = Path(file_path)
    ensure_dir(file_path.parent)
    np.save(file_path, data)
