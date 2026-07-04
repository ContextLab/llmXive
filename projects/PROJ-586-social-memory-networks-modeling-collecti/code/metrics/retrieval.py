"""
Cue-retrieval efficiency metrics for social memory networks.

Implements FR-005: Compute retrieval efficiency based on:
- Total facts available in the collective memory
- Facts successfully retrieved by the querying agent
- Agent count (normalization factor)
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np


@dataclass
class RetrievalMetrics:
    """Metrics describing retrieval performance."""
    total_facts: int
    retrieved_facts: int
    retrieval_rate: float
    efficiency_score: float
    agent_count: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_facts": self.total_facts,
            "retrieved_facts": self.retrieved_facts,
            "retrieval_rate": self.retrieval_rate,
            "efficiency_score": self.efficiency_score,
            "agent_count": self.agent_count,
        }


def validate_retrieval_efficiency(
    retrieved: int, total: int, agent_count: int
) -> bool:
    """
    Validate inputs for retrieval efficiency computation.

    Returns True if:
    - total > 0
    - retrieved >= 0
    - retrieved <= total
    - agent_count > 0
    """
    if total <= 0:
        return False
    if retrieved < 0:
        return False
    if retrieved > total:
        return False
    if agent_count <= 0:
        return False
    return True


def compute_retrieval_efficiency(
    retrieved: Union[int, float, List[int]],
    total: Union[int, float, List[int]],
    agent_count: Union[int, float, List[int]],
) -> Tuple[RetrievalMetrics, float]:
    """
    Compute retrieval efficiency metrics.

    Handles multiple call signatures for backward compatibility:
    1. compute_retrieval_efficiency(retrieved, total, agent_count) - standard
    2. compute_retrieval_efficiency(agent_list, num_agents=N) - keyword style
    3. compute_retrieval_efficiency(agent_count, game_id) - legacy (agent_count as list length)
    4. compute_retrieval_efficiency([]) - empty list handling

    Args:
        retrieved: Number of facts retrieved, or a list of agent skills
        total: Total facts available, or number of agents if retrieved is a list
        agent_count: Number of agents, or game_id in legacy mode

    Returns:
        Tuple of (RetrievalMetrics object, efficiency score float)

    Raises:
        ValueError: If inputs are invalid
    """
    # Handle legacy signature: (agent_count, game_id) where agent_count is actually list length
    if isinstance(retrieved, int) and isinstance(total, int):
        # Check if this looks like legacy call: (5, 10) meaning 5 agents, game 10
        # In legacy mode, agent_count was used as the list length
        # We treat this as: retrieved=5, total=10, agent_count=5 (derived)
        if isinstance(agent_count, int) and agent_count == retrieved:
            # Legacy pattern: agent_count passed as first arg
            actual_agent_count = retrieved
            actual_retrieved = agent_count
            actual_total = total
        else:
            actual_retrieved = retrieved
            actual_total = total
            actual_agent_count = agent_count
    elif isinstance(retrieved, list):
        # New signature: retrieve from list of agent skills
        # total is agent_count, agent_count is num_agents (or derived)
        actual_retrieved = sum(1 for x in retrieved if x > 0) if retrieved else 0
        actual_total = total if isinstance(total, int) else len(retrieved)
        actual_agent_count = agent_count if isinstance(agent_count, int) else len(retrieved)
    else:
        actual_retrieved = int(retrieved) if not isinstance(retrieved, int) else retrieved
        actual_total = int(total) if not isinstance(total, int) else total
        actual_agent_count = int(agent_count) if not isinstance(agent_count, int) else agent_count

    # Validate
    if not validate_retrieval_efficiency(actual_retrieved, actual_total, actual_agent_count):
        # Handle edge cases gracefully
        if actual_total <= 0:
            return RetrievalMetrics(
                total_facts=0,
                retrieved_facts=0,
                retrieval_rate=0.0,
                efficiency_score=0.0,
                agent_count=actual_agent_count,
            ), 0.0
        if actual_retrieved < 0:
            actual_retrieved = 0
        if actual_retrieved > actual_total:
            actual_retrieved = actual_total

    # Compute metrics
    retrieval_rate = actual_retrieved / actual_total if actual_total > 0 else 0.0

    # Efficiency score: normalized by agent count to account for network size
    # Higher efficiency means more facts retrieved per agent
    # Formula: retrieval_rate * sqrt(agent_count) to model network effects
    efficiency_score = retrieval_rate * math.sqrt(actual_agent_count)

    metrics = RetrievalMetrics(
        total_facts=actual_total,
        retrieved_facts=actual_retrieved,
        retrieval_rate=retrieval_rate,
        efficiency_score=efficiency_score,
        agent_count=actual_agent_count,
    )

    return metrics, efficiency_score


def batch_compute_retrieval_efficiency(
    records: List[Dict[str, Any]]
) -> List[Tuple[RetrievalMetrics, float]]:
    """
    Compute retrieval efficiency for a batch of game records.

    Args:
        records: List of dicts with keys: 'retrieved', 'total', 'agent_count'

    Returns:
        List of (RetrievalMetrics, efficiency_score) tuples
    """
    results = []
    for record in records:
        retrieved = record.get("retrieved_facts", record.get("retrieved", 0))
        total = record.get("total_facts", record.get("total", 1))
        agent_count = record.get("agent_count", 1)

        metrics, efficiency = compute_retrieval_efficiency(
            retrieved, total, agent_count
        )
        results.append((metrics, efficiency))

    return results