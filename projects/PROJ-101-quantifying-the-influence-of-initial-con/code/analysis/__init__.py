"""
Minimal initialisation for the analysis package.

The sub‑modules (baseline, ftle, regression, boundedness, etc.) are imported
lazily by the user or the CLI.  Keeping this ``__init__`` lightweight ensures
that ``import code.analysis`` succeeds even if optional heavy dependencies
(e.g. pandas, statsmodels) are unavailable or if a sub‑module contains
import‑time bugs that are not required for the basic package import.
"""

# Expose the configuration accessor – relative import works because this file
# lives in ``code/analysis`` and the config module is ``code/config.py``.
from ..config import get_full_config  # noqa: F401

__all__ = [
    "get_full_config",
]
