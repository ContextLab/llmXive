"""Retrieval efficiency metric for social memory networks."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, Any, List, Optional

@dataclass
class RetrievalMetrics:
    """Metrics for retrieval efficiency in a game."""
    retrieved_count: int = 0
    total_queries: int = 0
    agent_count: int = 0
    efficiency: float = 0.0

    def __format__(self, format_spec: str) -> str:
        """Support format strings by delegating to the efficiency float."""
        if format_spec:
            return format(self.efficiency, format_spec)
        return str(self.efficiency)

    def __float__(self) -> float:
        """Convert to float for compatibility."""
        return self.efficiency


def validate_retrieval_efficiency(retrieved: int, total: int, agent_count: int) -> bool:
    """Validate retrieval efficiency inputs."""
    if retrieved < 0 or total < 0 or agent_count <= 0:
        return False
    if retrieved > total:
        return False
    return True


def compute_retrieval_efficiency(
    retrieved: int | None = None,
    total: int | None = None,
    agents: int | List[int] | None = None,
    agent_count: int | None = None,
    game_id: int | None = None,
) -> Tuple[RetrievalMetrics, float]:
    """
    Compute retrieval efficiency metric.

    Supports multiple call signatures for backward compatibility:
    1. compute_retrieval_efficiency(retrieved, total, agents) - positional
    2. compute_retrieval_efficiency(retrieved=..., total=..., agents=...) - keyword
    3. compute_retrieval_efficiency(agent_count, game_id) - legacy (ignored)

    Args:
        retrieved: Number of successfully retrieved items
        total: Total number of queries
        agents: Agent count (int or list of agent IDs)
        agent_count: Alternative name for agent count
        game_id: Legacy parameter (ignored)

    Returns:
        Tuple of (RetrievalMetrics object, efficiency float in [0, 1])
    """
    # Handle positional args: compute_retrieval_efficiency(retrieved, total, agents)
    if retrieved is not None and total is not None and agents is not None:
        num_agents = agents if isinstance(agents, int) else len(agents) if isinstance(agents, list) else 1
        if not validate_retrieval_efficiency(retrieved, total, num_agents):
            raise ValueError(f"Invalid inputs: retrieved={retrieved}, total={total}, agents={num_agents}")
        
        efficiency = retrieved / total if total > 0 else 0.0
        metrics = RetrievalMetrics(
            retrieved_count=retrieved,
            total_queries=total,
            agent_count=num_agents,
            efficiency=efficiency
        )
        return metrics, efficiency

    # Handle keyword args with agent_count
    if retrieved is not None and total is not None and agent_count is not None:
        if not validate_retrieval_efficiency(retrieved, total, agent_count):
            raise ValueError(f"Invalid inputs: retrieved={retrieved}, total={total}, agent_count={agent_count}")
        
        efficiency = retrieved / total if total > 0 else 0.0
        metrics = RetrievalMetrics(
            retrieved_count=retrieved,
            total_queries=total,
            agent_count=agent_count,
            efficiency=efficiency
        )
        return metrics, efficiency

    # Legacy: compute_retrieval_efficiency(agent_count, game_id)
    # Return neutral metrics
    metrics = RetrievalMetrics(
        retrieved_count=0,
        total_queries=0,
        agent_count=1,
        efficiency=0.0
    )
    return metrics, 0.0
