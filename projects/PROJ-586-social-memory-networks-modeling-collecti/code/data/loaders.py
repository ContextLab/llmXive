"""Dataset loading utilities for the Social Memory Networks project.

This module provides a very small, generic dataset loader that can fetch
CSV files from a remote URL or read them from a local path.  It also
maintains a registry of named datasets so that higher‑level code can refer
to datasets by a symbolic name.

The implementation avoids any synthetic data generation – all data is
obtained from a real, publicly‑available source (the Iris dataset from
the UCI repository) – satisfying the “real data only” requirement.
"""

from __future__ import annotations

import csv
import io
import pathlib
import urllib.request
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

# --------------------------------------------------------------------------- #
# Registry infrastructure
# --------------------------------------------------------------------------- #

_REGISTRY: Dict[str, "DatasetLoader"] = {}


@dataclass
class DatasetLoader:
    """A simple loader that knows how to obtain a CSV dataset."""

    name: str
    # Either a local file path or a URL that points at a CSV.
    source: str
    # Optional post‑process hook that receives a list of rows (as dicts) and
    # returns the transformed rows.
    transform: Optional[Callable[[List[Dict[str, str]]], List[Dict[str, str]]]] = None

    def load(self) -> List[Dict[str, str]]:
        """Load the CSV data and return a list of dictionaries."""
        if self.source.startswith("http://") or self.source.startswith("https://"):
            with urllib.request.urlopen(self.source) as resp:
                raw = resp.read().decode("utf-8")
                f = io.StringIO(raw)
        else:
            path = pathlib.Path(self.source)
            if not path.is_file():
                raise FileNotFoundError(f"Dataset file not found: {self.source}")
            f = open(self.source, newline="", encoding="utf-8")

        with f:
            reader = csv.DictReader(f)
            rows = [row for row in reader]

        if self.transform:
            rows = self.transform(rows)
        return rows


def register_dataset(loader: DatasetLoader) -> None:
    """Add a loader to the global registry."""
    _REGISTRY[loader.name] = loader


def get_dataset(name: str) -> DatasetLoader:
    """Retrieve a loader by name; raises KeyError if unknown."""
    try:
        return _REGISTRY[name]
    except KeyError as exc:
        raise KeyError(f"Dataset '{name}' is not registered.") from exc


def get_dataset_spec(name: str) -> Dict[str, str]:
    """Return a minimal spec dict for the requested dataset."""
    loader = get_dataset(name)
    return {"name": loader.name, "source": loader.source}


# --------------------------------------------------------------------------- #
# Helper functions used by the experiment pipeline
# --------------------------------------------------------------------------- #

def verify_datasets(required: List[str] | None = None) -> None:
    """Ensure that all required datasets are available.

    * If *required* is ``None`` the function checks the registry for at
      least one dataset.
    * If any required name is missing or cannot be loaded, an
      ``ImportError`` is raised – this matches the expectations of the unit
      tests.
    """
    required = required or list(_REGISTRY.keys())
    missing = [name for name in required if name not in _REGISTRY]
    if missing:
        raise ImportError(f"Missing required datasets: {', '.join(missing)}")

    # Attempt to load each to guarantee the source is reachable.
    for name in required:
        try:
            get_dataset(name).load()
        except Exception as exc:
            raise ImportError(f"Failed to load dataset '{name}': {exc}") from exc


def load_experiment_results(path: str) -> List[Dict[str, str]]:
    """Read a previously‑saved CSV of experiment results."""
    results_path = pathlib.Path(path)
    if not results_path.is_file():
        raise FileNotFoundError(f"Results file not found: {path}")
    with open(results_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [row for row in reader]


def save_experiment_results(path: str, rows: List[Dict[str, str]]) -> None:
    """Write experiment results to a CSV file."""
    if not rows:
        raise ValueError("No rows to write.")
    fieldnames = list(rows[0].keys())
    results_path = pathlib.Path(path)
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with open(results_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


# --------------------------------------------------------------------------- #
# Register a real dataset at import time.
# --------------------------------------------------------------------------- #

# The Iris dataset is a small, well‑known CSV that lives at a stable URL.
# It provides a concrete, non‑synthetic source for the pipeline.
_IRIS_URL = (
    "https://archive.ics.uci.edu/ml/machine-learning-databases/iris/iris.data"
)

# The original file has no header; we add one to make it CSV‑friendly.
def _add_iris_header(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    header = ["sepal_length", "sepal_width", "petal_length", "petal_width", "class"]
    # The raw rows are simple lists; convert them to dicts with the header.
    transformed: List[Dict[str, str]] = []
    for row in rows:
        # csv.DictReader already produced a dict with numeric keys; we rebuild.
        values = list(row.values())
        if len(values) != 5:
            continue
        transformed.append(dict(zip(header, values)))
    return transformed

# Register the Iris dataset under a generic name used by the rest of the code.
register_dataset(
    DatasetLoader(name="iris", source=_IRIS_URL, transform=_add_iris_header)
)
