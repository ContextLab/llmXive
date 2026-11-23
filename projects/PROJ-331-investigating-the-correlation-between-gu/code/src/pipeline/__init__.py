"""Pipeline package initializer.

This module provides lazy attribute access to sub‑modules so that importing
``code.src.pipeline`` does not immediately import heavy optional
dependencies (e.g. ``scikit_bio`` used in ``preprocess``).  The lazy loader
returns the requested sub‑module the first time it is accessed.

Example
-------
>>> from code.src.pipeline import slopes
>>> slopes.compute_taxon_slopes(...)
"""
import importlib
import sys
from types import ModuleType
from typing import Any

__all__ = [
    "ingest",
    "preprocess",
    "slopes",
    "correlation",
    "mixed_effects",
    "permutation",
    "run_correlation_only",
    "run_us3",
    "__main__",
]

_module_cache: dict[str, ModuleType] = {}

def __getattr__(name: str) -> Any:
    """Lazily import sub‑modules on first attribute access."""
    if name not in __all__:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    if name in _module_cache:
        return _module_cache[name]

    module = importlib.import_module(f".{name}", __name__)
    _module_cache[name] = module
    return module

def __dir__() -> list[str]:
    return sorted(list(globals().keys()) + __all__)
