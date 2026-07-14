"""
Load the *real* NumPy implementation from the environment, bypassing the
project‑level ``code/numpy`` shim package that exists only to satisfy import
ordering constraints.

The module imports the genuine NumPy distribution (installed via pip) and
re‑exports all of its public attributes so that ``import numpy as np`` works
as expected throughout the code base.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from types import ModuleType


def _load_real_numpy() -> ModuleType:
    """
    Locate and load the genuine NumPy package from ``site‑packages``.

    Returns
    -------
    ModuleType
        The real NumPy module.
    """
    # Scan ``sys.path`` for entries that look like a site‑packages directory.
    for entry in sys.path:
        if not entry:
            continue
        if "site-packages" not in entry:
            continue
        # Attempt to find a spec for the *real* NumPy inside this entry.
        spec = importlib.util.find_spec("numpy", [entry])
        if spec is None or spec.origin is None:
            continue
        # Guard against accidentally picking up the shim (which lives under the
        # project ``code/numpy`` directory).
        if os.path.abspath(os.path.dirname(__file__)) in os.path.abspath(spec.origin):
            continue
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[assignment]
        return module
    raise ImportError("Real NumPy package not found in site‑packages.")


_real_numpy = _load_real_numpy()

# Re‑export everything so ``import numpy`` behaves like the genuine package.
globals().update(_real_numpy.__dict__)
