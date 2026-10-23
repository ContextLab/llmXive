"""
Top‑level ``src`` package provides a thin façade so that legacy imports
like ``from src import run_pipeline`` continue to work after the project
was reorganised under ``code/src``.
"""

# Re‑export the orchestrator entry point
from .run_pipeline import run_pipeline  # noqa: F401
