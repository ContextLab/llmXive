"""Utility functions for file I/O handling across the project."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence, Union

import pandas as pd


def ensure_dir(path: Union[str, Path]) -> Path:
    """Make sure the parent directory of *path* exists.

    Returns the absolute ``Path`` instance for convenience.
    """
    p = Path(path).expanduser().resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def load_csv(path: Union[str, Path]) -> list[dict[str, Any]]:
    """Load a CSV file into a list of dictionaries (one per row)."""
    p = Path(path).expanduser().resolve()
    with p.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def save_csv(
    path: Union[str, Path],
    data: Union[Sequence[Mapping[str, Any]], pd.DataFrame],
    *,
    header: bool = True,
    quoting: int = csv.QUOTE_MINIMAL,
) -> None:
    """Write *data* to *path* as CSV.

    ``data`` may be a list of mapping objects (e.g. ``list[dict]``) or a
    :class:`pandas.DataFrame`.  The function creates any missing parent
    directories automatically.
    """
    p = ensure_dir(path)
    if isinstance(data, pd.DataFrame):
        data.to_csv(p, index=False, header=header, quoting=quoting)
        return

    # Assume an iterable of mappings.
    if not data:
        # Write only the header if ``header=True`` and there is no data.
        if header:
            p.write_text("")
        return

    fieldnames = list(data[0].keys())
    with p.open(mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=quoting)
        if header:
            writer.writeheader()
        for row in data:
            writer.writerow(row)


def load_json(path: Union[str, Path]) -> Any:
    """Load a JSON file and return the parsed Python object."""
    p = Path(path).expanduser().resolve()
    with p.open(encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Union[str, Path], obj: Any, *, indent: int = 2) -> None:
    """Serialize *obj* as JSON to *path*."""
    p = ensure_dir(path)
    with p.open(mode="w", encoding="utf-8") as f:
        json.dump(obj, f, indent=indent, ensure_ascii=False)


def save_dataframe(
    path: Union[str, Path],
    df: pd.DataFrame,
    *,
    index: bool = False,
    header: bool = True,
    quoting: int = csv.QUOTE_MINIMAL,
) -> None:
    """Convenient wrapper around ``DataFrame.to_csv`` that also ensures the directory exists."""
    ensure_dir(path)
    df.to_csv(path, index=index, header=header, quoting=quoting)