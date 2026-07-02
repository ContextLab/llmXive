"""
Public export surface for the ``metrics`` package.

The module re‑exports the key metric functions so that callers can simply
import ``metrics`` and access ``compute_specialization_index``,
``compute_retrieval_rate`` and ``compute_retrieval_efficiency``.
"""

from .specialization import (
    SpecializationMetrics,
    compute_specialization_index,
    compute_game_level_specialization,
    validate_specialization_index,
)
from .retrieval import (
    RetrievalMetrics,
    compute_retrieval_rate,
    compute_retrieval_efficiency,
)

__all__ = [
    "SpecializationMetrics",
    "compute_specialization_index",
    "compute_game_level_specialization",
    "validate_specialization_index",
    "RetrievalMetrics",
    "compute_retrieval_rate",
    "compute_retrieval_efficiency",
]