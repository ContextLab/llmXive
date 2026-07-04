"""Retrieval efficiency metrics."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple, Any, List, Optional


@dataclass
class RetrievalMetrics:
    """Metrics for retrieval efficiency."""
    retrieval_rate: float
    efficiency_score: float
    avg_retrieval_time: float = 0.0


def validate_retrieval_efficiency(retrieved: int, total: int, agents: Any) -> bool:
    """Validate retrieval efficiency inputs."""
    if not isinstance(retrieved, int) or retrieved < 0:
        return False
    if not isinstance(total, int) or total < 0:
        return False
    if retrieved > total:
        return False
    if isinstance(agents, int) and agents <= 0:
        return False
    if isinstance(agents, list) and len(agents) == 0:
        return False
    return True


def compute_retrieval_efficiency(*args: Any, **kwargs: Any) -> Tuple[RetrievalMetrics, float]:
    """Compute retrieval efficiency metric.
    
    Accepts multiple call patterns:
    1. compute_retrieval_efficiency(retrieved, total, agents) - positional
    2. compute_retrieval_efficiency(retrieved=..., total=..., agents=...) - keyword
    3. compute_retrieval_efficiency(agent_count, game_id) - legacy (ignored)
    """
    retrieved = None
    total = None
    agents = None
    
    # Handle positional arguments
    if len(args) >= 1:
        retrieved = args[0]
    if len(args) >= 2:
        total = args[1]
    if len(args) >= 3:
        agents = args[2]
    
    # Handle keyword arguments (override positional)
    if 'retrieved' in kwargs:
        retrieved = kwargs['retrieved']
    if 'total' in kwargs:
        total = kwargs['total']
    if 'agents' in kwargs:
        agents = kwargs['agents']
    
    # Default values if not provided
    if retrieved is None:
        retrieved = 0
    if total is None:
        total = 1
    if agents is None:
        agents = 3
    
    # Normalize agents count
    agent_count = agents
    if isinstance(agents, list):
        agent_count = len(agents)
    
    # Validate
    if not validate_retrieval_efficiency(retrieved, total, agent_count):
        raise ValueError(f"Invalid retrieval inputs: retrieved={retrieved}, total={total}, agents={agent_count}")
    
    # Compute metrics
    retrieval_rate = retrieved / total if total > 0 else 0.0
    
    # Efficiency: penalize based on agent count (more agents = harder to retrieve)
    base_efficiency = retrieval_rate
    agent_penalty = 1.0 / (1.0 + 0.1 * agent_count)
    efficiency_score = base_efficiency * agent_penalty
    
    metrics = RetrievalMetrics(
        retrieval_rate=retrieval_rate,
        efficiency_score=efficiency_score,
        avg_retrieval_time=0.0
    )
    
    return metrics, efficiency_score
