"""
src package initializer
-----------------------
This module makes the core pipeline components importable directly from the
top‑level ``src`` package, as required by the integration tests and future
orchestration code.
"""

# Re‑export the CLI module so that ``from src import run_pipeline`` yields the
# module object containing ``main``.
from . import run_pipeline as run_pipeline  # noqa: F401

# Export the orchestrator function defined in ``pipeline.py``.
from .pipeline import run_pipeline as orchestrator  # noqa: F401

__all__ = ["run_pipeline", "orchestrator"]
