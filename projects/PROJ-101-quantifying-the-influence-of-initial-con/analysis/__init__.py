"""
Top‑level shim package for ``analysis`` imports.

The original implementation lives under ``code/analysis``.  To allow
test modules that import ``analysis.<module>`` (e.g. ``analysis.ftle``)
we expose the ``code/analysis`` directory as part of this package's
``__path__``.  This avoids relative‑import errors such as
``ImportError: attempted relative import beyond top‑level package``.
"""

import importlib.util
import sys
from pathlib import Path

# Resolve the location of the real implementation under ``code/analysis``.
_root = Path(__file__).resolve().parent.parent  # project root
_code_analysis = _root / "code" / "analysis"

if _code_analysis.is_dir():
    # Extend this package's search path so submodules are found there.
    __path__.append(str(_code_analysis))

# Optionally expose a few common symbols for convenience.
# Users can still import the full submodules (e.g., ``analysis.ftle``).
def __getattr__(name):
    # Lazy import of submodules when accessed as attributes.
    try:
        module = importlib.import_module(f"analysis.{name}")
        return module
    except ModuleNotFoundError as exc:
        raise AttributeError(f"module 'analysis' has no attribute '{name}'") from exc