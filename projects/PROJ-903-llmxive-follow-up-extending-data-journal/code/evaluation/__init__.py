"""
Evaluation module for the llmXive automated science pipeline.

This package contains utilities for:
- Bias measurement (Confirmation Bias, SC-002)
- Blinding logic (source label removal)
- Expert panel simulation and Kappa checks
- Rubric scoring for Narrative Depth (SC-001)
- Verification traceability auditing
"""

from .bias import calculate_confirmation_bias
from .blinding import strip_source_labels, generate_blinded_pairs
from .rubric import calculate_narrative_depth_score
from .traceability import audit_query_citations, calculate_traceability_metrics

__all__ = [
    "calculate_confirmation_bias",
    "strip_source_labels",
    "generate_blinded_pairs",
    "calculate_narrative_depth_score",
    "audit_query_citations",
    "calculate_traceability_metrics",
]