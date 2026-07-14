"""Utility functions for safe CSV/JSON I/O."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence, Union

import pandas as pd


def ensure_dir(path: Path) -> None:
    """Create ``path`` (including parents) if it does not already exist."""
    path.mkdir(parents=True, exist_ok=True)


def load_csv(path: Union[str, Path]) -> pd.DataFrame:
    """Load a CSV file into a ``pandas.DataFrame``."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"CSV file not found: {path}")
    return pd.read_csv(path)


def save_csv(df: pd.DataFrame, path: Union[str, Path]) -> None:
    """Write a ``DataFrame`` to CSV, creating the parent directory if needed."""
    path = Path(path)
    ensure_dir(path.parent)
    df.to_csv(path, index=False)


def load_json(path: Union[str, Path]) -> Any:
    """Load a JSON file."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"JSON file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(obj: Any, path: Union[str, Path]) -> None:
    """Serialise ``obj`` as JSON."""
    path = Path(path)
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def save_dataframe(df: pd.DataFrame, path: Union[str, Path]) -> None:
    """Alias for ``save_csv`` – kept for backward compatibility."""
    save_csv(df, path)