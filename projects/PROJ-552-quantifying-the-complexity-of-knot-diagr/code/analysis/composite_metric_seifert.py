"""Deprecated module – use ``analysis.metrics`` instead."""
import warnings

warnings.warn(
    "Module 'analysis.composite_metric_seifert' is deprecated; import from 'analysis.metrics' instead.",
    DeprecationWarning,
    stacklevel=2,
)

from .metrics import (
    novel_composite_metric as novel_composite_metric_seifert,
    evaluate_novel_metric_correlation,
)

__all__ = ["novel_composite_metric_seifert", "evaluate_novel_metric_correlation"]