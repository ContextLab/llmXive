from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Tuple, Any, List

@dataclass
class RetrievalMetrics:
    retrieved: int
    total: int
    baseline: float
    normalized: float

def compute_retrieval_efficiency(
    retrieved: int,
    total: int,
    agents: List[int] | int,
) -> Tuple[RetrievalMetrics, float]:
    """
    Compute retrieval efficiency.

    ``retrieved`` and ``total`` are integer counts. ``agents`` may be a list of
    agent identifiers or an integer count of agents.
    """
    if isinstance(agents, int):
        agent_count = agents
    else:
        agent_count = len(agents)

    baseline = 1.0 / agent_count if agent_count > 0 else 0.0
    efficiency = (retrieved / total) if total > 0 else 0.0
    normalized = efficiency / baseline if baseline > 0 else 0.0

    metrics = RetrievalMetrics(
        retrieved=retrieved,
        total=total,
        baseline=baseline,
        normalized=normalized,
    )
    return metrics, efficiency

# Validation helper used elsewhere
def validate_retrieval_efficiency(eff: float) -> bool:
    return 0.0 <= eff <= 1.0