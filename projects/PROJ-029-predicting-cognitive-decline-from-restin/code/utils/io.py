"""
I/O utilities for file handling.
Ensures compatibility with all callers (T017, T019, etc.).
"""
from __future__ import annotations

import csv
import json
import os
import pickle
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence, Union

from utils.logger import get_logger

logger = get_logger("io_utils")


def ensure_dir(path: Union[str, Path]) -> None:
    """Ensure the directory of the given path exists."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)


def load_csv(path: Union[str, Path]) -> list[dict]:
    """Load a CSV file into a list of dictionaries."""
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)


def save_csv(data: Iterable[Mapping[str, Any]], path: Union[str, Path]) -> None:
    """Save a list of dictionaries to a CSV file."""
    ensure_dir(path)
    if not data:
        # Write empty file with no headers if data is empty
        with open(path, 'w', encoding='utf-8') as f:
            pass
        return

    fieldnames = list(data[0].keys())
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def load_json(path: Union[str, Path]) -> Any:
    """Load a JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data: Any, path: Union[str, Path]) -> None:
    """Save data to a JSON file."""
    ensure_dir(path)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)


def load_pickle(path: Union[str, Path]) -> Any:
    """Load a pickle file."""
    with open(path, 'rb') as f:
        return pickle.load(f)


def save_pickle(data: Any, path: Union[str, Path]) -> None:
    """Save data to a pickle file."""
    ensure_dir(path)
    with open(path, 'wb') as f:
        pickle.dump(data, f)


def save_text(text: str, path: Union[str, Path]) -> None:
    """Save text to a file."""
    ensure_dir(path)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
