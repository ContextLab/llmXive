"""
Shim package that forwards all attribute accesses to the genuine NumPy
implementation loaded via ``code.numpy_real``.

This file exists because the repository contains a top‑level ``numpy`` package
(likely added for namespace reasons). Importing pandas (or any other library
that depends on NumPy) would otherwise resolve to this stub, which lacks
required attributes such as ``__version__`` and leads to import errors.

By delegating to the real NumPy distribution at import time we restore
compatibility while keeping the original package name unchanged.
"""

from __future__ import annotations

# Load the real NumPy implementation and expose its symbols.
from ..numpy_real import *  # noqa: F403,F401

# Ensure ``sys.modules['numpy']`` points to this shim (which now contains all
# real NumPy attributes).  This line is technically unnecessary because Python
# already registers the module under its own name, but it makes the intention
# explicit.
import sys

sys.modules[__name__] = sys.modules[__name__]