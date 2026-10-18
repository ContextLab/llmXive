"""Legacy wrapper for ``code.analysis``.

The analysis module is not required for the thin quick‑start run,
but the wrapper ensures that ``python -m src.llmxive.analysis`` works
if invoked later.
"""
from __future__ import annotations

# Forward everything – the analysis implementation lives in ``code.analysis``.
from code.analysis import *  # noqa: F403,F401

# Export the names that ``code.analysis`` defines (dynamic import).
# ``__all__`` will be populated by the imported module.
