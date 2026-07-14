from __future__ import annotations

import csv
import json
import pickle
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence, Union

def ensure_dir(path: Union[str, Path]) -> Path:
    """Ensure directory exists."""
    p = Path(path)
    if not p.exists():
        p.mkdir(parents=True, exist_ok=True)
    return p

def load_csv(path: Union[str, Path], delimiter: str = ',') -> list[dict]:
    """Load CSV file into list of dicts."""
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        return list(reader)

def save_csv(path: Union[str, Path], data: Iterable[Mapping], delimiter: str = ',') -> None:
    """Save list of dicts to CSV."""
    ensure_dir(path)
    with open(path, 'w', newline='', encoding='utf-8') as f:
        if not data:
            return
        fieldnames = list(data[0].keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
        writer.writeheader()
        writer.writerows(data)

def load_json(path: Union[str, Path]) -> Any:
    """Load JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(path: Union[str, Path], data: Any) -> None:
    """Save data to JSON file."""
    ensure_dir(path)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)

def load_pickle(path: Union[str, Path]) -> Any:
    """Load pickle file."""
    with open(path, 'rb') as f:
        return pickle.load(f)

def save_pickle(path: Union[str, Path], data: Any) -> None:
    """Save data to pickle file."""
    ensure_dir(path)
    with open(path, 'wb') as f:
        pickle.dump(data, f)
