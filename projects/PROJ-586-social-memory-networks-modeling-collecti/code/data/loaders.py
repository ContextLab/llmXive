"""Dataset loaders with real data sources. NO synthetic data generation."""
from __future__ import annotations

import csv
import pathlib
import random
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable

# Registry for real datasets
_DATASET_REGISTRY: Dict[str, Callable[[], List[Dict[str, Any]]]] = {}
_SYNTHETIC_FALLBACK_ENABLED = False

@dataclass
class DatasetSpec:
    name: str
    description: str
    source: str  # URL or package name
    file_path: Optional[str] = None

def register_dataset(name: str):
    def decorator(func: Callable[[], List[Dict[str, Any]]]):
        if name in _DATASET_REGISTRY:
            raise ValueError(f"Dataset {name} already registered")
        _DATASET_REGISTRY[name] = func
        return func
    return decorator

def get_dataset(name: str) -> List[Dict[str, Any]]:
    if name not in _DATASET_REGISTRY:
        if _SYNTHETIC_FALLBACK_ENABLED:
            # Spec explicitly forbids synthetic fallback for research results
            # Raising error to enforce real data usage
            raise ValueError(f"Dataset '{name}' not found. Synthetic fallback is NOT authorized for research results.")
        raise ValueError(f"Dataset '{name}' not registered.")
    return _DATASET_REGISTRY[name]()

def enable_synthetic_fallback():
    global _SYNTHETIC_FALLBACK_ENABLED
    _SYNTHETIC_FALLBACK_ENABLED = True

def disable_synthetic_fallback():
    global _SYNTHETIC_FALLBACK_ENABLED
    _SYNTHETIC_FALLBACK_ENABLED = False

def get_dataset_spec(name: str) -> Optional[DatasetSpec]:
    # Placeholder for spec lookup
    if name in _DATASET_REGISTRY:
        return DatasetSpec(name=name, description="Registered dataset", source="local")
    return None

def verify_datasets(names: List[str]) -> bool:
    missing = [n for n in names if n not in _DATASET_REGISTRY]
    if missing:
        raise ValueError(f"Missing datasets: {missing}")
    return True

def load_experiment_results(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Results file not found: {path}")
    results = []
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(row)
    return results

def save_experiment_results(path: Path, results: List[Dict[str, Any]]):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not results:
        raise ValueError("Cannot save empty results list")
    fieldnames = list(results[0].keys())
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

# Register a real dataset loader if available, otherwise raise on get
@register_dataset("wikidata_sample")
def load_wikidata_sample() -> List[Dict[str, Any]]:
    # In a real scenario, this would fetch from a real source
    # For this task, we rely on the pre-existing data files
    raise NotImplementedError("Real dataset loader requires external source. Use existing CSVs.")
