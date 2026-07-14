"""
Compatibility shim for the real NumPy package.

The project inadvertently included a top‑level ``numpy`` package that shadowed the
genuine NumPy installation, causing import errors in libraries such as pandas
and scipy (e.g. ``module 'numpy' has no attribute '__version__'``).

This ``__init__`` forwards all attributes of the genuine NumPy library (installed
in the environment) to the shadowed package, making ``import numpy`` behave as
expected throughout the code‑base.
"""
import importlib
import sys

# Import the real NumPy implementation from the helper module.
# ``numpy_real`` lives in ``code/numpy_real.py`` and simply does:
#     import numpy as _real_numpy
# exposing the real NumPy object as ``_real_numpy``.
_real_numpy_module = importlib.import_module('numpy_real')
_real_numpy = getattr(_real_numpy_module, '_real_numpy', None)

if _real_numpy is None:
    raise ImportError("Failed to locate the real NumPy implementation via numpy_real.")

# Populate the current module's globals with everything from the real NumPy.
globals().update(_real_numpy.__dict__)

# Ensure that subsequent ``import numpy`` statements resolve to this shim which
# now contains the full NumPy API.
sys.modules.setdefault('numpy', _real_numpy)
