"""
Top‑level ``src`` package provides a thin façade so that legacy imports
like ``from src import run_pipeline`` continue to work after the project
was reorganised under ``code/src``.

The original implementation imported ``run_pipeline`` eagerly, which caused
heavy downstream imports (e.g. the HCP download module) to be executed at
import time. This triggered an ``ImportError`` in environments where the
optional ``pyarrow`` dependency of the ``datasets`` library was unavailable.
To keep the package lightweight and to allow unit tests that only need
sub‑modules (such as ``src.stats.power_pre``) to import safely, the import
is now performed lazily via ``__getattr__``.
"""

__all__ = ["run_pipeline"]

def __getattr__(name):
    if name == "run_pipeline":
        # Lazy import to avoid pulling in heavy dependencies unless
        # the orchestrator is actually needed.
        from .run_pipeline import run_pipeline
        return run_pipeline
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
