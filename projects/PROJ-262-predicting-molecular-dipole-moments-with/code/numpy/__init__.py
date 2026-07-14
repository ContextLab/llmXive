"""
Shim module to expose the real NumPy implementation.

The project previously introduced a custom ``code/numpy`` package that attempted
to import a ``numpy_real`` helper, which caused a circular import and broke any
downstream ``import numpy as np`` statements.  This file now simply forwards all
attributes to the genuine NumPy package from the Python environment, ensuring
that the rest of the codebase works without modification.
"""

import importlib
import sys

# Load the real NumPy implementation from the environment.
_real_numpy = importlib.import_module('numpy')

# Populate the current module's globals with NumPy's public attributes.
globals().update(_real_numpy.__dict__)

# Replace the entry in ``sys.modules`` so subsequent ``import numpy`` statements
# receive the genuine NumPy module rather than this shim.
sys.modules[__name__] = _real_numpy
