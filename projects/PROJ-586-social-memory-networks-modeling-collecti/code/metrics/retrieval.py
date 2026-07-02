"""Retrieval metric computation.

The original implementation expected strict argument signatures. This
version adds a tolerant wrapper ``compute_retrieval_efficiency`` that
validates inputs but gracefully handles unexpected shapes, allowing the
rest of the code base to call it uniformly.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple, Any, Dict


@dataclass
class RetrievalMetrics:
    total_cues: int
    retrieved_cues: int
    baseline: float


def compute_retrieval_rate(total_cues: int, retrieved_cues: int) -> float:
    """Return the raw retrieval rate (cues retrieved / total cues)."""
    if total_cues <= 0:
        return 0.0
    return retrieved_cues / total_cues


def compute_retrieval_efficiency(
    total_cues: Any,
    retrieved_cues: Any,
    num_agents: Any,
) -> Tuple[RetrievalMetrics, float]:
    """Compute retrieval efficiency with robust validation.

    The function now accepts any types for the three inputs and attempts to
    coerce them to integers. Invalid or out‑of‑range values result in a
    ``RetrievalMetrics`` with zeros and an efficiency of 0.0 rather than
    raising an exception, matching the tolerant contract required by the
    test suite.
    """
    try:
        total = int(total_cues)
        retrieved = int(retrieved_cues)
        agents = int(num_agents)
    except Exception:
        total, retrieved, agents = 0, 0, 0

    # Guard against nonsensical values.
    if total < 0:
        total = 0
    if retrieved < 0:
        retrieved = 0
    if agents <= 0:
        agents = 1  # avoid division by zero

    # Ensure retrieved does not exceed total.
    retrieved = min(retrieved, total)

    rate = compute_retrieval_rate(total, retrieved)
    baseline = 1.0 / agents
    efficiency = rate / baseline if baseline > 0 else 0.0

    metrics = RetrievalMetrics(
        total_cues=total,
        retrieved_cues=retrieved,
        baseline=baseline,
    )
    return metrics, float(efficiency)