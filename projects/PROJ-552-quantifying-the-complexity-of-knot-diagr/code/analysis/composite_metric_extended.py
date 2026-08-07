"""Deprecated module – use ``analysis.metrics`` instead."""
import warnings

warnings.warn(
    "Module 'analysis.composite_metric_extended' is deprecated; import from 'analysis.metrics' instead.",
    DeprecationWarning,
    stacklevel=2,
)

from .metrics import composite_complexity, evaluate_correlation

__all__ = ["composite_complexity", "evaluate_correlation"]
