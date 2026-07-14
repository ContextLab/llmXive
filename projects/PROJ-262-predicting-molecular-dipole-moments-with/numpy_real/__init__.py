"""Compatibility shim for the project's custom ``numpy`` wrapper.

The repository contains a top‑level ``numpy`` package that attempts to
lazily import the real NumPy implementation as ``numpy_real``.  Some
execution environments raise ``ModuleNotFoundError: No module named
'numpy_real'`` because the shim does not exist.  Providing this module
restores the expected import path without altering the existing
``numpy`` package logic.

The shim simply re‑exports the genuine NumPy namespace.
"""
import numpy as _real_numpy

# Re‑export everything so ``import numpy_real as np`` works.
globals().update(_real_numpy.__dict__)
