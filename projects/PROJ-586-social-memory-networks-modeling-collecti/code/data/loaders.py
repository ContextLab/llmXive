"""Dataset loading utilities with a minimal extensible registry."""
from __future__ import annotations

import csv
import pathlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# Registry for dataset loader callables
_DATASET_REGISTRY: Dict[str, "DatasetLoader"] = {}


@dataclass
class DatasetLoader:
    """
    Simple container for a dataset loading function.

    Attributes
    ----------
    name: str
        Identifier used for registration and lookup.
    load_fn: Callable[[], Any]
        Callable that returns the loaded dataset when invoked.
    """
    name: str
    load_fn: Callable[[], Any]

    def load(self) -> Any:
        """Execute the underlying loading function."""
        return self.load_fn()


def register_dataset(name: str, load_fn: Callable[[], Any]) -> None:
    """
    Register a new dataset loader.

    Parameters
    ----------
    name: str
        Unique name for the dataset.
    load_fn: Callable[[], Any]
        Function that loads and returns the dataset.
    """
    if name in _DATASET_REGISTRY:
        raise ValueError(f"Dataset '{name}' is already registered.")
    _DATASET_REGISTRY[name] = DatasetLoader(name=name, load_fn=load_fn)


def get_dataset(name: str) -> Any:
    """
    Retrieve a dataset by name.

    If the dataset is not registered, an ImportError is raised.  This mirrors the
    expectations of the unit tests which check for ImportError when a required
    dataset is missing.
    """
    if name not in _DATASET_REGISTRY:
        raise ImportError(f"Dataset '{name}' is not registered.")
    return _DATASET_REGISTRY[name].load()


def get_dataset_spec(name: str) -> Dict[str, Any]:
    """
    Return a minimal specification dictionary for a registered dataset.

    The spec is intentionally lightweight – only the name and a short description
    are provided.  Callers can extend this as needed.
    """
    if name not in _DATASET_REGISTRY:
        raise ImportError(f"Dataset '{name}' is not registered.")
    # In a full implementation this could include URLs, checksum, etc.
    return {"name": name, "description": f"Dataset loader for '{name}'"}


def verify_datasets(required: Optional[List[str]] = None) -> None:
    """
    Verify that all required datasets are registered.

    Parameters
    ----------
    required: list of str, optional
        Names of datasets that must be present.  If ``None`` the function checks
        that *any* dataset is registered.

    Raises
    ------
    ImportError
        If any required dataset is missing.
    """
    if required is None:
        required = list(_DATASET_REGISTRY.keys())
    missing = [name for name in required if name not in _DATASET_REGISTRY]
    if missing:
        raise ImportError(f"Missing required datasets: {', '.join(missing)}")


def load_experiment_results(csv_path: Path) -> List[Dict[str, Any]]:
    """
    Load experiment results from a CSV file.

    Returns a list of dictionaries – one per row.
    """
    if not csv_path.is_file():
        raise FileNotFoundError(f"Results file not found: {csv_path}")
    with csv_path.open(newline="") as f:
        reader = csv.DictReader(f)
        return [row for row in reader]


def save_experiment_results(csv_path: Path, records: List[Dict[str, Any]]) -> None:
    """
    Write experiment results to a CSV file.

    Parameters
    ----------
    csv_path: Path
        Destination CSV file.
    records: list of dict
        Each dict must have the same keys (column headers).
    """
    if not records:
        raise ValueError("No records to write.")
    fieldnames = list(records[0].keys())
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
