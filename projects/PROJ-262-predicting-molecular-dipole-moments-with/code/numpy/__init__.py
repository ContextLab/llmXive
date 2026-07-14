"""
Shim module to expose the real NumPy package under the project ``code/numpy`` package.
Some parts of the codebase import ``numpy`` via ``import numpy as np`` which resolves
to this package because ``code`` is added to ``PYTHONPATH``.  The original shim tried
to re‑export symbols from a non‑existent ``numpy_real`` module, causing an import
error.  The implementation below simply imports the genuine NumPy library and
re‑exports all of its public symbols.
"""

import importlib
import sys
from types import ModuleType

# Load the real NumPy package (the one installed in the environment)
_real_numpy: ModuleType = importlib.import_module("numpy")

# Re‑export everything from the real NumPy into this shim's namespace.
# ``globals()`` is the module dict for this ``code.numpy`` package.
globals().update(_real_numpy.__dict__)

# Ensure that ``sys.modules['numpy']`` points to the real package so that any
# subsequent ``import numpy`` statements (outside of the ``code`` package) receive
# the genuine implementation.
sys.modules["numpy"] = _real_numpy

# Clean up temporary names.
del importlib, sys, ModuleType, _real_numpy
