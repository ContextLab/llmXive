"""Deprecated module – use ``analysis.metrics`` instead."""
import warnings

warnings.warn(
    "Module 'analysis.composite_metric_novel' is deprecated; import from 'analysis.metrics' instead.",
    DeprecationWarning,
    stacklevel=2,
)

from .metrics import novel_composite_metric

__all__ = ["novel_composite_metric"]
