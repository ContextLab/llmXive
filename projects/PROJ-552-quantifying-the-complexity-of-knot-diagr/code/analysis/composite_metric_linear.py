"""Deprecated module – use ``analysis.metrics`` instead."""
import warnings

warnings.warn(
    "Module 'analysis.composite_metric_linear' is deprecated; import from 'analysis.metrics' instead.",
    DeprecationWarning,
    stacklevel=2,
)

from .metrics import compute_linear_composite, evaluate_composite_metric

__all__ = ["compute_linear_composite", "evaluate_composite_metric"]
