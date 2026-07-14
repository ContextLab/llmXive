"""
Shim module to expose the real NumPy package while this repository also contains a
``code/numpy`` package that would otherwise shadow the installed NumPy.

The implementation temporarily removes the directory of this shim from ``sys.path``,
imports the genuine NumPy distribution, and then re‑exports all of its public
symbols. This avoids the recursive import problem that previously caused a
``RecursionError`` during module loading.
"""

from __future__ import annotations

import importlib
import pathlib
import sys
from types import ModuleType

def _load_real_numpy() -> ModuleType:
    """
    Import the real NumPy package, bypassing this shim's location.

    Returns
    -------
    ModuleType
        The genuine NumPy module.
    """
    # Resolve the absolute path of this shim's directory.
    shim_dir = pathlib.Path(__file__).resolve().parent

    # Preserve the original sys.path.
    original_path = list(sys.path)
    try:
        # Remove the shim directory from sys.path so that ``import numpy`` finds the
        # installed package instead of recursing back into this file.
        sys.path = [p for p in sys.path if pathlib.Path(p).resolve() != shim_dir]

        # Import the real NumPy package.
        real_numpy = importlib.import_module("numpy")
        return real_numpy
    finally:
        # Restore the original sys.path regardless of success/failure.
        sys.path = original_path

# Load the genuine NumPy and re‑export its public API.
_real_numpy = _load_real_numpy()
globals().update(_real_numpy.__dict__)
