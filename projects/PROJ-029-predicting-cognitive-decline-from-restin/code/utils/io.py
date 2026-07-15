"""
I/O utility functions for loading and saving data.
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
    """Ensure directory exists."""
    path = Path(path)
    if path.suffix:  # It's a file, get parent
        path = path.parent
    path.mkdir(parents=True, exist_ok=True)
    return path

def load_csv(path: Union[str, Path]) -> List[Dict[str, Any]]:
    """Load CSV file into list of dictionaries."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")
    
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def save_csv(data: List[Dict[str, Any]], path: Union[str, Path]) -> None:
    """Save list of dictionaries to CSV."""
    path = Path(path)
    ensure_dir(path)
    
    if not data:
        # Write empty file
        with open(path, 'w', newline='', encoding='utf-8') as f:
            f.write("")
        return
    
    fieldnames = list(data[0].keys())
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def load_json(path: Union[str, Path]) -> Any:
    """Load JSON file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data: Any, path: Union[str, Path]) -> None:
    """Save data to JSON file."""
    path = Path(path)
    ensure_dir(path)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)

def load_pickle(path: Union[str, Path]) -> Any:
    """Load pickle file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Pickle file not found: {path}")
    
    with open(path, 'rb') as f:
        return pickle.load(f)

def save_pickle(data: Any, path: Union[str, Path]) -> None:
    """Save data to pickle file."""
    path = Path(path)
    ensure_dir(path)
    
    with open(path, 'wb') as f:
        pickle.dump(data, f)

def save_text(text: str, path: Union[str, Path]) -> None:
    """Save text to file."""
    path = Path(path)
    ensure_dir(path)
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)

def load_numpy(path: Union[str, Path]) -> np.ndarray:
    """Load NumPy file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"NumPy file not found: {path}")
    
    return np.load(path)

def save_numpy(data: np.ndarray, path: Union[str, Path]) -> None:
    """Save NumPy array to file."""
    path = Path(path)
    ensure_dir(path)
    
    np.save(path, data)
