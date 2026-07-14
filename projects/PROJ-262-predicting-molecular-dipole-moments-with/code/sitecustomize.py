"""
Site customization to ensure that the real NumPy package is loaded before any
other libraries (e.g., pandas, scipy) attempt to import it.

The project contains a placeholder ``code/numpy`` package that interferes with
the standard NumPy import, causing ``AttributeError: module 'numpy' has no
attribute '__version__'``.  This module patches ``sys.modules`` so that the
real NumPy distribution (exposed via ``code/numpy_real.py``) is used
throughout the project.
"""
from __future__ import annotations

import importlib
import sys
from types import ModuleType

def _load_real_numpy() -> ModuleType:
    """
    Load the genuine NumPy implementation from ``numpy_real`` and register it
    under the name ``numpy`` in ``sys.modules``.
    """
    # Import the helper module that re‑exports the real NumPy package.
    real_numpy = importlib.import_module("numpy_real")
    # Ensure the alias is available for subsequent imports.
    sys.modules["numpy"] = real_numpy
    return real_numpy

def _ensure_numpy_is_compatible() -> None:
    """
    Verify that the currently imported ``numpy`` module has the ``__version__``
    attribute.  If it does not (which is the case for the placeholder package),
    replace it with the real implementation.
    """
    try:
        import numpy as np  # type: ignore
        # The placeholder package lacks ``__version__``.
        if not hasattr(np, "__version__"):
            raise AttributeError
    except Exception:
        # Load and register the genuine NumPy distribution.
        _load_real_numpy()

# Execute the compatibility shim as soon as the interpreter starts.
_ensure_numpy_is_compatible()
