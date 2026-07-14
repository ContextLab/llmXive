"""
Helper module that provides a direct reference to the genuine NumPy
implementation.

The original stub did not actually import NumPy, which caused the shim
in ``code/numpy/__init__.py`` to fail.  This file now simply imports the
real NumPy package and re‑exports it under the name ``numpy_real``.
"""

import importlib

# Import the real NumPy package from the environment.
_real_numpy = importlib.import_module("numpy")

# Re‑export the module's public symbols.
globals().update(_real_numpy.__dict__)

# Make the module itself available as ``numpy_real`` for any code that
# performs ``import numpy_real``.
import sys

sys.modules["numpy_real"] = _real_numpy
