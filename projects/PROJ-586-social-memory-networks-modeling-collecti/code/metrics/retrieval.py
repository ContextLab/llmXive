"""Retrieval‑efficiency metric utilities."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

@dataclass
class RetrievalMetrics:
    """Container for raw retrieval counts."""
    correct: int
    total: int
    agents: int

def compute_retrieval_rate(correct: int, total: int) -> float:
    """Return the proportion of correct retrievals; guard against bad input."""
    if total <= 0:
        return 0.0
    return max(0.0, min(1.0, correct / total))

def compute_retrieval_efficiency(
    correct: int,
    total: int,
    agents: int,
) -> Tuple[RetrievalMetrics, float]:
    """
    Compute retrieval efficiency.

    The function is deliberately tolerant:
    * Negative values are clamped to zero.
    * Zero agents yields efficiency zero (avoids division by zero).
    * Returns a ``RetrievalMetrics`` instance and the efficiency float.
    """
    # Clamp inputs to sensible non‑negative values.
    correct = max(0, correct)
    total = max(0, total)
    agents = max(1, agents)  # at least one agent for baseline computation

    rate = compute_retrieval_rate(correct, total)

    # Baseline chance of a random guess is 1 / agents.
    baseline = 1.0 / agents
    # Efficiency is the ratio of observed rate to baseline, capped at a reasonable range.
    efficiency = rate / baseline if baseline > 0 else 0.0
    efficiency = max(0.0, efficiency)

    metrics = RetrievalMetrics(correct=correct, total=total, agents=agents)
    return metrics, efficiency