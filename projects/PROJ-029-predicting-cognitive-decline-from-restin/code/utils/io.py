"""
IO utilities used across the project.
Added missing ``load_pickle`` helper required by the sensitivity analysis.
"""

from __future__ import annotations

import csv
import json
import pickle
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence, Union

import pandas as pd


def ensure_dir(dir_path: Union[str, Path]) -> None:
    """Create a directory if it does not exist."""
    path = Path(dir_path)
    path.mkdir(parents=True, exist_ok=True)


def load_csv(csv_path: Union[str, Path]) -> list[dict[str, Any]]:
    """Read a CSV file into a list of dictionaries."""
    path = Path(csv_path)
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [row for row in reader]


def save_csv(data: Sequence[Mapping[str, Any]], csv_path: Union[str, Path]) -> None:
    """Write a sequence of dicts to CSV."""
    if not data:
        raise ValueError("No data supplied to save_csv")
    path = Path(csv_path)
    ensure_dir(path.parent)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(data[0].keys()))
        writer.writeheader()
        for row in data:
            writer.writerow(row)


def load_json(json_path: Union[str, Path]) -> Any:
    """Load a JSON file."""
    path = Path(json_path)
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def save_json(obj: Any, json_path: Union[str, Path]) -> None:
    """Save an object as pretty‑printed JSON."""
    path = Path(json_path)
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def load_pickle(pickle_path: Union[str, Path]) -> Any:
    """Load a pickled Python object."""
    path = Path(pickle_path)
    with path.open("rb") as f:
        return pickle.load(f)


def save_pickle(obj: Any, pickle_path: Union[str, Path]) -> None:
    """Save an object using pickle."""
    path = Path(pickle_path)
    ensure_dir(path.parent)
    with path.open("wb") as f:
        pickle.dump(obj, f)