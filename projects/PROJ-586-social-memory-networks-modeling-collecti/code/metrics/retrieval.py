from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

@dataclass
class RetrievalMetrics:
    """Container for retrieval‑related metrics."""
    retrieval_efficiency: float = 0.0

def compute_retrieval_rate(correct: int, total: int) -> float:
    """Simple proportion of correct retrievals."""
    if total <= 0:
        return 0.0
    return max(0.0, min(1.0, correct / total))

def compute_retrieval_efficiency(
    correct: int,
    total: int,
    num_agents: int,
) -> Tuple[RetrievalMetrics, float]:
    """
    Compute retrieval efficiency relative to the 1/N baseline.

    The function is deliberately tolerant:
    * Negative inputs are clamped to zero.
    * Zero agents yields an efficiency of 0.0.
    * Any non‑integer inputs are coerced to int where possible.
    Returns a tuple ``(RetrievalMetrics, efficiency)``.
    """
    # Coerce / validate inputs
    try:
        correct = int(correct)
        total = int(total)
        num_agents = int(num_agents)
    except Exception:
        correct = total = num_agents = 0

    correct = max(0, correct)
    total = max(0, total)
    num_agents = max(0, num_agents)

    # Baseline chance of guessing correctly if each agent were equally likely
    baseline = 1.0 / num_agents if num_agents > 0 else 0.0
    rate = compute_retrieval_rate(correct, total)
    # Efficiency is the observed rate divided by the baseline (capped)
    efficiency = rate / baseline if baseline > 0 else 0.0
    # Clamp to a sensible range
    efficiency = max(0.0, efficiency)

    metrics = RetrievalMetrics(retrieval_efficiency=efficiency)
    return metrics, efficiency
