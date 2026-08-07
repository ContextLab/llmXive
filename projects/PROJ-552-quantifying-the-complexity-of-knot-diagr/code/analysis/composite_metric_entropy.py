"""Deprecated module – use ``analysis.metrics`` instead."""
import warnings

warnings.warn(
    "Module 'analysis.composite_metric_entropy' is deprecated; import from 'analysis.metrics' instead.",
    DeprecationWarning,
    stacklevel=2,
)

from .metrics import weighted_entropy_metric, compute_metric_from_diagram

__all__ = ["weighted_entropy_metric", "compute_metric_from_diagram"]
