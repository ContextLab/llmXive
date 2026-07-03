"""Dataset loading utilities with a minimal extensible registry and synthetic fallback.

This module implements FR-011: dataset loaders with synthetic fallback only.
It provides a registry pattern for dataset loaders and a controlled fallback
mechanism that generates minimal synthetic data ONLY when real datasets are
unavailable and fallback is explicitly enabled.

IMPORTANT: Synthetic data is NOT for primary analysis. It serves only as a
structural placeholder for testing pipeline connectivity when real data
sources are temporarily inaccessible.
"""
from __future__ import annotations

import csv
import pathlib
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# Registry for dataset loader callables
_DATASET_REGISTRY: Dict[str, "DatasetLoader"] = {}

# Fallback flag: if True, and no real dataset is found, generate synthetic data.
# This is the "synthetic fallback only" mechanism required by FR-011.
# DEFAULT IS FALSE to prevent accidental fabrication.
_USE_SYNTHETIC_FALLBACK: bool = False


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

    If the dataset is not registered, and synthetic fallback is enabled,
    generates a minimal synthetic dataset. Otherwise, raises ImportError.

    Parameters
    ----------
    name : str
        The name of the dataset to retrieve.

    Returns
    -------
    Any
        The loaded dataset.

    Raises
    ------
    ImportError
        If the dataset is not registered and fallback is disabled.
    """
    if name in _DATASET_REGISTRY:
        return _DATASET_REGISTRY[name].load()
    
    if _USE_SYNTHETIC_FALLBACK:
        # Generate synthetic fallback data ONLY when explicitly enabled
        return _generate_synthetic_fallback(name)
    
    raise ImportError(
        f"Dataset '{name}' is not registered. "
        f"Enable synthetic fallback via enable_synthetic_fallback() if this is a test environment."
    )


def _generate_synthetic_fallback(name: str) -> List[Dict[str, Any]]:
    """
    Generate a minimal synthetic dataset as a fallback.
    
    This is NOT for primary analysis but serves as a placeholder when
    real data is unavailable, ensuring the pipeline can run structure tests.
    The data is clearly marked as synthetic in the records.
    
    Parameters
    ----------
    name : str
        The name of the dataset being requested.
        
    Returns
    -------
    List[Dict[str, Any]]
        A list of synthetic records with explicit 'is_synthetic' flag.
    """
    records = []
    # Generate a small, deterministic set of synthetic records (10)
    # Seed is fixed for reproducibility of the fallback structure
    rng = random.Random(42)
    
    for i in range(10):
        record = {
            "game_id": f"synthetic_{name}_{i:03d}",
            "agent_count": rng.randint(3, 7),
            "context_condition": "full",
            "specialization_index": rng.uniform(0.1, 0.9),
            "retrieval_efficiency": rng.uniform(0.2, 0.95),
            "is_synthetic": True,
            "source": "synthetic_fallback",
            "note": "This is synthetic fallback data. Do not use for research conclusions."
        }
        records.append(record)
    return records


def enable_synthetic_fallback() -> None:
    """Enable synthetic data generation when real datasets are missing.
    
    WARNING: This should only be used in test environments or when real
    data sources are temporarily unavailable. Results from synthetic data
    must be clearly labeled as such.
    """
    global _USE_SYNTHETIC_FALLBACK
    _USE_SYNTHETIC_FALLBACK = True


def disable_synthetic_fallback() -> None:
    """Disable synthetic data generation (strict mode).
    
    In strict mode, any attempt to load an unregistered dataset will raise
    an ImportError. This is the default and recommended setting for research.
    """
    global _USE_SYNTHETIC_FALLBACK
    _USE_SYNTHETIC_FALLBACK = False


def get_dataset_spec(name: str) -> Dict[str, Any]:
    """
    Return a minimal specification dictionary for a registered dataset.

    The spec is intentionally lightweight – only the name and a short description
    are provided.  Callers can extend this as needed.

    Parameters
    ----------
    name : str
        The name of the dataset.

    Returns
    -------
    Dict[str, Any]
        A specification dictionary.

    Raises
    ------
    ImportError
        If the dataset is not registered and fallback is disabled.
    """
    if name in _DATASET_REGISTRY:
        return {"name": name, "description": f"Dataset loader for '{name}'"}
    
    if _USE_SYNTHETIC_FALLBACK:
        return {
            "name": name, 
            "description": f"Synthetic fallback for '{name}'", 
            "is_synthetic": True,
            "warning": "This is synthetic fallback data."
        }
    
    raise ImportError(f"Dataset '{name}' is not registered.")


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
        If any required dataset is missing (and fallback is disabled).
    """
    if required is None:
        required = list(_DATASET_REGISTRY.keys())
    
    missing = [name for name in required if name not in _DATASET_REGISTRY]
    
    if missing:
        if _USE_SYNTHETIC_FALLBACK:
            # Allow missing datasets if fallback is enabled, but log warning
            import logging
            logging.warning(
                f"Missing required datasets: {', '.join(missing)}. "
                f"Synthetic fallback is enabled, so these will be generated as placeholders."
            )
        else:
            raise ImportError(f"Missing required datasets: {', '.join(missing)}")


def load_experiment_results(csv_path: Path) -> List[Dict[str, Any]]:
    """
    Load experiment results from a CSV file.

    Returns a list of dictionaries – one per row.

    Parameters
    ----------
    csv_path : Path
        Path to the CSV file.

    Returns
    -------
    List[Dict[str, Any]]
        List of result records.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
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
    
    # Ensure all records have the same keys
    fieldnames = list(records[0].keys())
    for rec in records:
        if set(rec.keys()) != set(fieldnames):
            raise ValueError("All records must have identical keys.")
    
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
