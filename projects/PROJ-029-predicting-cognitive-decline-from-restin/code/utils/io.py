from __future__ import annotations

import csv
import json
import os
import pickle
from pathlib import Path
from typing import Any, Dict, List, Union

import numpy as np

def ensure_dir(directory: Union[str, Path]) -> Path:
    """Ensure a directory exists, creating it if necessary."""
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    return path

def load_csv(filepath: Union[str, Path]) -> List[Dict[str, str]]:
    """Load a CSV file into a list of dictionaries."""
    with open(filepath, newline='') as f:
        reader = csv.DictReader(f)
        return list(reader)

def save_csv(filepath: Union[str, Path], data: List[Dict[str, Any]], fieldnames: List[str] = None):
    """Save a list of dictionaries to a CSV file."""
    filepath = Path(filepath)
    ensure_dir(filepath.parent)
    
    if not data:
        # Create empty file with headers if needed
        with open(filepath, 'w', newline='') as f:
            if fieldnames:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
        return

    if fieldnames is None:
        fieldnames = list(data[0].keys())
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def load_json(filepath: Union[str, Path]) -> Any:
    """Load a JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)

def save_json(filepath: Union[str, Path], data: Any):
    """Save data to a JSON file."""
    filepath = Path(filepath)
    ensure_dir(filepath.parent)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def load_pickle(filepath: Union[str, Path]) -> Any:
    """Load a pickle file."""
    with open(filepath, 'rb') as f:
        return pickle.load(f)

def save_pickle(filepath: Union[str, Path], data: Any):
    """Save data to a pickle file."""
    filepath = Path(filepath)
    ensure_dir(filepath.parent)
    with open(filepath, 'wb') as f:
        pickle.dump(data, f)

def save_text(filepath: Union[str, Path], text: str):
    """Save text to a file."""
    filepath = Path(filepath)
    ensure_dir(filepath.parent)
    with open(filepath, 'w') as f:
        f.write(text)

def load_numpy(filepath: Union[str, Path]) -> np.ndarray:
    """Load a .npy file."""
    return np.load(filepath)

def save_numpy(filepath: Union[str, Path], data: np.ndarray):
    """Save a numpy array to a .npy file."""
    filepath = Path(filepath)
    ensure_dir(filepath.parent)
    np.save(filepath, data)
