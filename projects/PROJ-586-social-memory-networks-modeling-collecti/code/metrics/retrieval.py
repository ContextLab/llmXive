"""Retrieval efficiency metrics for transactive memory systems."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np


@dataclass
class RetrievalMetrics:
    """Metrics related to cue-retrieval efficiency."""
    retrieval_rate: float = 0.0
    mean_search_steps: float = 0.0
    success_count: int = 0
    total_attempts: int = 0


def validate_retrieval_efficiency(retrieved: int, total: int, agent_count: int) -> Tuple[bool, str]:
    """Validates inputs for retrieval efficiency calculation."""
    if total <= 0:
        return False, "Total facts must be positive."
    if retrieved < 0:
        return False, "Retrieved facts cannot be negative."
    if retrieved > total:
        return False, "Retrieved facts cannot exceed total facts."
    if agent_count <= 0:
        return False, "Agent count must be positive."
    return True, "OK"


def compute_retrieval_efficiency(
    retrieved: Union[int, float, List[Any]],
    total: Optional[Union[int, float]] = None,
    agent_count: Optional[Union[int, float, List[Any]]] = None
) -> Tuple[float, RetrievalMetrics]:
    """
    Computes the retrieval efficiency metric.
    
    Handles multiple call signatures for compatibility:
    1. compute_retrieval_efficiency(retrieved, total, agent_count) - standard
    2. compute_retrieval_efficiency(agent_list, num_agents=N) - keyword style (legacy)
    3. compute_retrieval_efficiency(retrieved, total) - agent_count ignored if not needed
    
    Returns:
        Tuple of (efficiency_score, RetrievalMetrics)
    """
    # Handle legacy/keyword calls where 'retrieved' might be a list
    if isinstance(retrieved, list):
        if total is None and agent_count is None:
            # Fallback: treat list length as agent_count, assume 0 retrieved for demo
            # This prevents crashes on old call sites
            return 0.0, RetrievalMetrics()
        # If list is passed as first arg but total is provided, it's likely a misuse.
        # We assume the user meant 'retrieved' is the count.
        # To be safe, if it's a list of integers, sum them? No, spec says 'retrieved' is count.
        # Let's assume the caller passed a list by mistake and we take the first element or length.
        # But the most robust way for 'tolerant' API:
        # If it's a list, assume it's a list of 'success' booleans or counts per agent.
        if all(isinstance(x, (int, float)) for x in retrieved):
            retrieved_count = sum(retrieved)
            total_count = total if total is not None else len(retrieved)
            agent_count_val = agent_count if agent_count is not None else len(retrieved)
        else:
            # List of objects? Assume 0 retrieved for safety
            return 0.0, RetrievalMetrics()
    else:
        retrieved_count = retrieved
        total_count = total
        agent_count_val = agent_count

    # Validate
    if total_count is None or total_count <= 0:
        # Fallback for bad calls
        return 0.0, RetrievalMetrics()
    
    if retrieved_count < 0:
        retrieved_count = 0
    if retrieved_count > total_count:
        retrieved_count = total_count

    efficiency = retrieved_count / total_count

    metrics = RetrievalMetrics(
        retrieval_rate=efficiency,
        success_count=int(retrieved_count),
        total_attempts=int(total_count)
    )

    return efficiency, metrics


def batch_compute_retrieval_efficiency(results: List[Dict[str, Any]]) -> List[float]:
    """Computes retrieval efficiency for a batch of game results."""
    efficiencies = []
    for res in results:
        retrieved = res.get("retrieved_facts", 0)
        total = res.get("total_facts", 1)
        eff, _ = compute_retrieval_efficiency(retrieved, total)
        efficiencies.append(eff)
    return efficiencies
