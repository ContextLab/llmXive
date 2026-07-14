"""
Site customization to ensure that the real NumPy package is used.

Some project modules (e.g., `numpy_real.py`) may unintentionally shadow the
actual NumPy installation, causing libraries like pandas to import an
incomplete stub that lacks required attributes such as ``__version__``.

This file forces the import of the genuine NumPy package and registers it
in ``sys.modules`` under the name ``numpy`` before any other imports occur.
"""

import importlib
import sys

# If ``numpy`` is already mapped to a stub (e.g., ``numpy_real``) or missing,
# import the real NumPy package from the environment and replace the entry.
_numpy_mod = sys.modules.get("numpy")
if (
    _numpy_mod is None
    or getattr(_numpy_mod, "__name__", "") == "numpy_real"
    or not hasattr(_numpy_mod, "__version__")
):
    # Import the actual NumPy package from site‑packages.
    real_numpy = importlib.import_module("numpy")
    sys.modules["numpy"] = real_numpy

# Clean up temporary names.
del importlib, sys, _numpy_mod, real_numpy
