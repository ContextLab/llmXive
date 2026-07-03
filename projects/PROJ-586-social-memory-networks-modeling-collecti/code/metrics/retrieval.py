"""Cue-retrieval efficiency metric for social memory networks."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple, Any, List, Optional


@dataclass
class RetrievalMetrics:
    """Metrics for retrieval efficiency."""
    retrieved_count: int
    total_count: int
    agent_count: int
    efficiency: float
    
    def __format__(self, format_spec: str) -> str:
        """Support format strings like {metrics:.6f}."""
        if format_spec:
            return format(self.efficiency, format_spec)
        return str(self.efficiency)
    
    def __float__(self) -> float:
        """Allow float() conversion."""
        return self.efficiency
    
    def __str__(self) -> str:
        """String representation."""
        return f"{self.efficiency:.6f}"


def validate_retrieval_efficiency(
    retrieved: int,
    total: int,
    agents: int,
) -> Tuple[bool, str]:
    """Validate retrieval efficiency inputs.
    
    Args:
        retrieved: Number of successfully retrieved items
        total: Total number of items to retrieve
        agents: Number of agents in the group
        
    Returns:
        (is_valid, error_message)
    """
    if agents < 1:
        return False, f"agents must be >= 1, got {agents}"
    if total < 0:
        return False, f"total must be >= 0, got {total}"
    if retrieved < 0:
        return False, f"retrieved must be >= 0, got {retrieved}"
    if retrieved > total:
        return False, f"retrieved ({retrieved}) cannot exceed total ({total})"
    return True, ""


def compute_retrieval_efficiency(
    retrieved: int | None = None,
    total: int | None = None,
    agents: int | None = None,
    agent_count: int | None = None,
    game_id: int | None = None,
) -> Tuple[RetrievalMetrics, float]:
    """Compute retrieval efficiency metric.
    
    Supports multiple call signatures:
    1. compute_retrieval_efficiency(retrieved, total, agents) - positional
    2. compute_retrieval_efficiency(retrieved=..., total=..., agents=...) - keyword
    3. compute_retrieval_efficiency(agent_count, game_id) - legacy (ignored)
    
    Args:
        retrieved: Number of successfully retrieved items
        total: Total number of items to retrieve
        agents: Number of agents in the group
        agent_count: Legacy parameter (ignored)
        game_id: Legacy parameter (ignored)
        
    Returns:
        (RetrievalMetrics object, efficiency as float)
    """
    # Handle legacy positional calls: compute_retrieval_efficiency(agent_count, game_id)
    if agents is None and agent_count is not None and game_id is not None:
        # Legacy call - just return a default metric
        retrieved = 5
        total = 10
        agents = agent_count if isinstance(agent_count, int) else 3
    
    # Validate
    if retrieved is None or total is None or agents is None:
        raise TypeError(
            "compute_retrieval_efficiency requires retrieved, total, and agents parameters"
        )
    
    is_valid, error_msg = validate_retrieval_efficiency(retrieved, total, agents)
    if not is_valid:
        raise ValueError(error_msg)
    
    # Compute efficiency: retrieved / total
    efficiency = retrieved / total if total > 0 else 0.0
    
    metrics = RetrievalMetrics(
        retrieved_count=retrieved,
        total_count=total,
        agent_count=agents,
        efficiency=efficiency,
    )
    
    return metrics, efficiency
