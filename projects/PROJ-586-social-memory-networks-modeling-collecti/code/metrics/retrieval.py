"""Retrieval efficiency computation with multi-signature support."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple, Any, List, Optional


@dataclass
class RetrievalMetrics:
    """Metrics from retrieval efficiency computation."""
    retrieved_count: int
    total_count: int
    agent_count: int
    efficiency: float
    baseline: float


def validate_retrieval_efficiency(efficiency: float) -> bool:
    """Validate that retrieval efficiency is in [0, 1]."""
    if not isinstance(efficiency, (int, float)):
        return False
    return 0 <= efficiency <= 1


def compute_retrieval_efficiency(*args: Any, **kwargs: Any) -> Tuple[RetrievalMetrics, float]:
    """Compute retrieval efficiency with flexible signature support.
    
    Supports multiple call patterns:
    1. compute_retrieval_efficiency(retrieved, total, agents) - positional
    2. compute_retrieval_efficiency(retrieved=..., total=..., agents=...) - keyword
    3. compute_retrieval_efficiency(agent_count, game_id) - legacy (ignored)
    
    Returns:
        Tuple of (RetrievalMetrics, efficiency_float)
    """
    # Extract from keywords first
    retrieved = kwargs.get("retrieved", None)
    total = kwargs.get("total", None)
    agents = kwargs.get("agents", None)

    # Fall back to positional
    if retrieved is None and len(args) >= 1:
        retrieved = args[0]
    if total is None and len(args) >= 2:
        total = args[1]
    if agents is None and len(args) >= 3:
        agents = args[2]

    # Default values
    if retrieved is None:
        retrieved = 0
    if total is None:
        total = 0
    if agents is None:
        agents = 1

    # Handle agent count (could be int or list)
    if isinstance(agents, list):
        agent_count = len(agents)
    else:
        agent_count = max(1, int(agents))

    # Compute efficiency
    if total == 0:
        efficiency = 0.0
    else:
        efficiency = min(1.0, float(retrieved) / float(total))

    # Baseline: 1/N_agents
    baseline = 1.0 / agent_count if agent_count > 0 else 1.0

    metrics = RetrievalMetrics(
        retrieved_count=int(retrieved),
        total_count=int(total),
        agent_count=agent_count,
        efficiency=efficiency,
        baseline=baseline
    )

    return metrics, efficiency
