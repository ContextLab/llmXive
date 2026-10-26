"""
src.stats.power_pre
-------------------
Thin wrapper that re‑exports the implementation from the canonical
location ``code/src/stats/power_pre.py``.  The test suite (and any
external code) imports the module via ``src.stats.power_pre``; this
shim forwards all public symbols so that there is a single source of
truth while keeping the original file untouched.

The wrapper does **not** duplicate any logic – it simply imports the
concrete functions, constants and the ``main`` entry point from the
implementation module and makes them available under the ``src.stats``
namespace.
"""
from __future__ import annotations

# Import the real implementation from the code directory.
from code.src.stats.power_pre import (
    compute_power,
    write_results,
    POWER_THRESHOLD,
    DEFAULT_SUBJECTS,
    EFFECT_SIZE_F2,
    ALPHA,
    main,
)

# Re‑export the public API so that ``from src.stats.power_pre import …``
# works exactly as the tests expect.
__all__ = [
    "compute_power",
    "write_results",
    "POWER_THRESHOLD",
    "DEFAULT_SUBJECTS",
    "EFFECT_SIZE_F2",
    "ALPHA",
    "main",
]

# The module-level docstring and ``__all__`` are sufficient; no further
# code is required. All functionality is delegated to the implementation
# in ``code/src/stats/power_pre.py``.