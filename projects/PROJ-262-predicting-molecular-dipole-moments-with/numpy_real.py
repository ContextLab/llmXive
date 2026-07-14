"""
Real NumPy shim module.

This module provides the actual NumPy package under the name ``numpy_real``.
It is used by the project's custom ``numpy`` package shim to load the real
NumPy implementation without causing import errors.
"""
import numpy as np

# Export the NumPy namespace so that ``import numpy_real as np`` works.
__all__ = ["np"]
