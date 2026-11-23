"""
Shim module that re‑exports the real data validation implementation.

The project’s source lives in ``code/preprocessing/data_validation.py``.
Tests expect to import ``preprocessing.data_validation``; this file simply
imports everything from the canonical location.
"""
from code.preprocessing.data_validation import *  # noqa: F401,F403
