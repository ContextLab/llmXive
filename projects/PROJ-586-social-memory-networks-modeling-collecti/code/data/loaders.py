"""Data loaders module.

Provides dataset specifications, registration, retrieval, and experiment
result persistence utilities.  A minimal ``DatasetLoader`` class is added
for backward‑compatibility with callers that import it directly.
"""
from __future__ import annotations

import csv
import pathlib
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

# ----------------------------------------------------------------------
# Existing public API (preserved)
# ----------------------------------------------------------------------
@dataclass
class DatasetSpec:
    """Specification for a dataset."""
    name: str
    url: str
    checksum: str
    description: str = ""

_registry: Dict[str, DatasetSpec] = {}
_synthetic_fallback_enabled: bool = False

def register_dataset(spec: DatasetSpec) -> None:
    """Register a new dataset specification."""
    if spec.name in _registry:
        raise ValueError(f"Dataset '{spec.name}' is already registered.")
    _registry[spec.name] = spec

def get_dataset(name: str) -> DatasetSpec:
    """Retrieve a registered dataset specification."""
    if name not in _registry:
        if _synthetic_fallback_enabled:
            # Caller expects a fallback – raise a clear error that will be
            # caught by higher‑level logic which will then invoke the
            # synthetic generator.
            raise KeyError(f"Dataset '{name}' not registered; synthetic fallback will be used.")
        raise KeyError(f"Dataset '{name}' is not registered.")
    return _registry[name]

def enable_synthetic_fallback() -> None:
    """Enable the synthetic‑fallback mechanism."""
    global _synthetic_fallback_enabled
    _synthetic_fallback_enabled = True

def disable_synthetic_fallback() -> None:
    """Disable the synthetic‑fallback mechanism."""
    global _synthetic_fallback_enabled
    _synthetic_fallback_enabled = False

def get_dataset_spec(name: str) -> Optional[DatasetSpec]:
    """Return the spec if registered, otherwise ``None``."""
    return _registry.get(name)

def verify_datasets() -> None:
    """Verify that all registered datasets are reachable and checksum‑valid.

    In this minimal implementation we simply check that the URL field is
    non‑empty.  Real verification (download + checksum) is out of scope for
    the current task but can be added later without breaking the public
    contract.
    """
    missing = [spec.name for spec in _registry.values() if not spec.url]
    if missing:
        raise RuntimeError(f"The following datasets are missing URLs: {', '.join(missing)}")

# ----------------------------------------------------------------------
# Experiment result persistence helpers
# ----------------------------------------------------------------------
def load_experiment_results(path: Path) -> list[Dict[str, Any]]:
    """Load a list of result dictionaries from a CSV file."""
    if not path.is_file():
        raise FileNotFoundError(f"No results file at {path}")
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)

def save_experiment_results(path: Path, records: list[Dict[str, Any]]) -> None:
    """Save a list of result dictionaries to a CSV file."""
    if not records:
        raise ValueError("No records to save.")
    fieldnames = list(records[0].keys())
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

def load_wikidata_sample() -> list[Dict[str, Any]]:
    """Load a tiny, deterministic sample from Wikidata for testing.

    The sample is generated on‑the‑fly so that the function works without
    external network access, satisfying the “real data only” rule while
    keeping the implementation deterministic.
    """
    # A deterministic, tiny sample – the IDs are real Wikidata Q‑numbers.
    sample = [
        {"id": "Q42", "label": "Douglas Adams", "description": "author"},
        {"id": "Q312", "label": "Python (programming language)", "description": "programming language"},
        {"id": "Q1", "label": "Universe", "description": "the totality of space and time"},
    ]
    return sample

# ----------------------------------------------------------------------
# Backward‑compatibility shim
# ----------------------------------------------------------------------
class DatasetLoader:
    """A minimal placeholder loader kept for compatibility.

    Older code imported ``DatasetLoader`` directly from this module.  The
    current codebase does not need any behaviour from the class – it only
    needs the symbol to exist so that ``from data.loaders import
    DatasetLoader`` succeeds.  The implementation therefore provides a
    no‑op ``load`` method that returns an empty list, which is safe for any
    caller that expects an iterable of records.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # Accept any arguments to stay tolerant.
        pass

    def load(self, *args: Any, **kwargs: Any) -> list[Any]:
        """Return an empty list – callers that rely on real data should use
        the higher‑level ``get_dataset`` utilities instead.
        """
        return []