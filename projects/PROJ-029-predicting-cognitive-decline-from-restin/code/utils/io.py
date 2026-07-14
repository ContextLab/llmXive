"""Utility functions for I/O operations used across the project."""
from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence, Union


def ensure_dir(path: Union[str, Path]) -> None:
    """Create a directory (including parents) if it does not exist."""
    Path(path).mkdir(parents=True, exist_ok=True)


def load_csv(path: Union[str, Path]) -> list[dict]:
    """Read a CSV file into a list of dictionaries."""
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def save_csv(path: Union[str, Path], rows: Sequence[Mapping[str, Any]]) -> None:
    """Write an iterable of mappings to a CSV file."""
    ensure_dir(Path(path).parent)
    if not rows:
        raise ValueError("No rows provided for CSV output.")
    fieldnames = list(rows[0].keys())
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def load_json(path: Union[str, Path]) -> Any:
    """Load JSON data from a file."""
    with open(path) as f:
        return json.load(f)


def save_json(path: Union[str, Path], data: Any) -> None:
    """Save a Python object as JSON."""
    ensure_dir(Path(path).parent)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_pickle(path: Union[str, Path]) -> Any:
    """Load a pickled Python object."""
    import pickle

    with open(path, "rb") as f:
        return pickle.load(f)


def save_pickle(path: Union[str, Path], obj: Any) -> None:
    """Save a Python object using pickle."""
    ensure_dir(Path(path).parent)
    import pickle

    with open(path, "wb") as f:
        pickle.dump(obj, f)


def save_text(path: Union[str, Path], text: str) -> None:
    """Write raw text to a file."""
    ensure_dir(Path(path).parent)
    with open(path, "w") as f:
        f.write(text)