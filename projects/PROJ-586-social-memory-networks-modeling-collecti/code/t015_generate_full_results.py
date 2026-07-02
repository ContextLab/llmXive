"""Core metric computation with flexible signatures."""
from __future__ import annotations

from typing import Any, List, Tuple, Union
from metrics.specialization import compute_specialization_index as _core_spec_index
from metrics.specialization import SpecializationMetrics
from metrics.retrieval import compute_retrieval_efficiency as _core_ret_eff
from metrics.retrieval import RetrievalMetrics


def compute_specialization_index(*args: Any, **kwargs: Any) -> Tuple[float, SpecializationMetrics]:
    """Wrapper for core specialization computation with flexible signatures."""
    return _core_spec_index(*args, **kwargs)


def compute_retrieval_efficiency(*args: Any, **kwargs: Any) -> Tuple[RetrievalMetrics, float]:
    """Wrapper for core retrieval computation with flexible signatures."""
    return _core_ret_eff(*args, **kwargs)
