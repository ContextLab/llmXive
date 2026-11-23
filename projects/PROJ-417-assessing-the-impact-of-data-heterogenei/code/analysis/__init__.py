"""
Analysis package for the meta-analysis heterogeneity simulation project.

NOTE: This package previously attempted to import ``analysis.estimators``,
which does not exist (estimators live in ``simulation.estimators``).
That broken import caused every ``python code/main.py`` invocation to
fail with ``ModuleNotFoundError``. This __init__ is intentionally minimal:
submodules (``analysis.metrics``, ``analysis.stats``) are imported
directly by consumers.
"""

__all__ = ["metrics", "stats"]
