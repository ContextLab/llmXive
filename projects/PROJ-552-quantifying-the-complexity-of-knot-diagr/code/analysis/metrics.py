"""Consolidated metrics module.

This module gathers all metric‑related functions that were previously
scattered across the ``composite_metric*`` modules.  Existing modules are
retained for backward compatibility but simply re‑export the symbols from
here.
"""
from __future__ import annotations

# Import the original implementations from their legacy modules.
# The imports are performed under private names to avoid polluting the
# public namespace before we deliberately expose the unified API.
from .composite_metric import combined_complexity_score as _combined_complexity_score
from .composite_metric_entropy import (
    weighted_entropy_metric as _weighted_entropy_metric,
    compute_metric_from_diagram as _compute_metric_from_diagram,
)
from .composite_metric_extended import (
    composite_complexity as _composite_complexity,
    evaluate_correlation as _evaluate_correlation,
)
from .composite_metric_linear import (
    compute_linear_composite as _compute_linear_composite,
    evaluate_composite_metric as _evaluate_composite_metric,
)
from .composite_metric_novel import novel_composite_metric as _novel_composite_metric_general
from .composite_metric_seifert import (
    novel_composite_metric as _novel_composite_metric_seifert,
    evaluate_novel_metric_correlation as _evaluate_novel_metric_correlation,
)

# Re‑export under a unified, documented namespace.
combined_complexity_score = _combined_complexity_score
weighted_entropy_metric = _weighted_entropy_metric
compute_metric_from_diagram = _compute_metric_from_diagram
composite_complexity = _composite_complexity
evaluate_correlation = _evaluate_correlation
compute_linear_composite = _compute_linear_composite
evaluate_composite_metric = _evaluate_composite_metric

# Two distinct “novel” metrics existed; we keep both with explicit names.
novel_composite_metric = _novel_composite_metric_general
novel_composite_metric_seifert = _novel_composite_metric_seifert
evaluate_novel_metric_correlation = _evaluate_novel_metric_correlation

__all__ = [
    "combined_complexity_score",
    "weighted_entropy_metric",
    "compute_metric_from_diagram",
    "composite_complexity",
    "evaluate_correlation",
    "compute_linear_composite",
    "evaluate_composite_metric",
    "novel_composite_metric",
    "novel_composite_metric_seifert",
    "evaluate_novel_metric_correlation",
]
