"""
Compatibility shim for the ``datasets`` library.

The repository previously contained a top‑level ``datasets.py`` stub that
shadowed the real HuggingFace ``datasets`` package, causing import failures
in the test suite (``import datasets`` did not expose ``__version__``).

This shim forwards all attribute access to the genuine ``datasets`` package
installed in the environment while also exposing ``__version__`` directly.
It is deliberately minimal – only the symbols required by the project
(currently ``load_dataset``) are forwarded, but any other attribute will be
lazily resolved via ``__getattr__``.
"""

import importlib
import os
import sys
from importlib import metadata
from types import ModuleType
from typing import Any

# Determine the version of the real ``datasets`` package.
try:
    __version__: str = metadata.version("datasets")
except Exception:  # pragma: no cover
    # If the package is not installed, raise a clear error.
    raise ImportError(
        "The real 'datasets' package is required but could not be found. "
        "Ensure it is installed via the project's requirements.txt."
    )

def _load_real_datasets() -> ModuleType:
    """
    Import the genuine ``datasets`` package, bypassing this shim.

    The project root (``os.getcwd()``) is normally the first entry in
    ``sys.path`` and contains this file, which would cause a recursive import.
    We temporarily remove the project root from ``sys.path`` so that Python
    can locate the external package installed in the virtual environment.
    """
    cwd = os.getcwd()
    original_path = list(sys.path)
    try:
        # Exclude the current working directory to avoid importing this file again.
        sys.path = [p for p in sys.path if p != cwd]
        real_module = importlib.import_module("datasets")
    finally:
        # Restore the original import path.
        sys.path = original_path
    return real_module

# Load the actual library once; subsequent attribute access is delegated.
_real_datasets = _load_real_datasets()

# Explicitly expose the most‑used function.
load_dataset = _real_datasets.load_dataset  # type: ignore

def __getattr__(name: str) -> Any:
    """
    Lazily forward any other attribute accesses to the real ``datasets``
    module. This mirrors the behaviour of ``import *`` without polluting the
    namespace unnecessarily.
    """
    return getattr(_real_datasets, name)

def __dir__() -> list:
    """
    Provide a helpful ``dir()`` implementation that includes both the shim
    attributes and those of the underlying library.
    """
    shim_attrs = ["__version__", "load_dataset", "__getattr__", "__dir__"]
    return sorted(set(shim_attrs + dir(_real_datasets)))