"""Utility I/O helpers used across the project."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence, Union

import pandas as pd


def ensure_dir(path: Union[str, Path]) -> Path:
    """Make sure a directory exists; return the Path object."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def load_csv(filepath: Union[str, Path]) -> list[dict[str, Any]]:
    """Load a CSV file and return a list of rows as dictionaries."""
    path = Path(filepath)
    if not path.is_file():
        raise FileNotFoundError(f"CSV file not found: {filepath}")
    with path.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return [dict(row) for row in reader]


def save_csv(
    data: Sequence[Mapping[str, Any]],
    filepath: Union[str, Path],
    *,
    header: Sequence[str] | None = None,
    mode: str = "w",
) -> None:
    """Write an iterable of mappings to a CSV file.

    Parameters
    ----------
    data: Sequence[Mapping[str, Any]]
        Rows to write. Each mapping must be dict‑like.
    filepath: Union[str, Path]
        Destination file.
    header: optional sequence of column names. If omitted, the keys of the first
        row are used.
    mode: file mode, default ``'w'`` (overwrite). ``'a'`` can be used for
        appending.
    """
    if not data:
        raise ValueError("No data provided to save_csv")
    path = Path(filepath)
    ensure_dir(path.parent)
    fieldnames = list(header) if header is not None else list(data[0].keys())
    with path.open(mode, newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if mode == "w":
            writer.writeheader()
        for row in data:
            writer.writerow(dict(row))


def load_json(filepath: Union[str, Path]) -> Any:
    """Load a JSON file."""
    path = Path(filepath)
    if not path.is_file():
        raise FileNotFoundError(f"JSON file not found: {filepath}")
    with path.open(encoding='utf-8') as f:
        return json.load(f)


def save_json(obj: Any, filepath: Union[str, Path], *, indent: int = 2) -> None:
    """Save an object as pretty‑printed JSON."""
    path = Path(filepath)
    ensure_dir(path.parent)
    with path.open('w', encoding='utf-8') as f:
        json.dump(obj, f, indent=indent, ensure_ascii=False)


def save_dataframe(df: pd.DataFrame, filepath: Union[str, Path], *, index: bool = False) -> None:
    """Save a pandas DataFrame to CSV."""
    path = Path(filepath)
    ensure_dir(path.parent)
    df.to_csv(path, index=index)