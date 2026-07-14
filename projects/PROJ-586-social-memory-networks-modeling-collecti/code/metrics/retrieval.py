"""
Cue-retrieval efficiency metrics.

Implements FR-005: Calculate proportion of successful retrievals vs. a theoretical baseline.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np


@dataclass
class RetrievalMetrics:
    """Container for retrieval efficiency metrics."""
    efficiency: float
    successful_retrievals: int
    total_queries: int
    agents: int
    theoretical_baseline: float
    error_rate: float = field(default=0.0)


def compute_retrieval_efficiency(
    successful: Union[int, List[int], None],
    total: Union[int, List[int], None],
    agents: Union[int, List[int]]
) -> Tuple[float, RetrievalMetrics]:
    """
    Compute cue-retrieval efficiency.

    Args:
        successful: Number of successful retrievals (int or list).
        total: Total number of queries (int or list). If None, assumed equal to successful (100% success).
        agents: Number of agents (int or list).

    Returns:
        Tuple of (efficiency_score, RetrievalMetrics object).

    FR-005: Calculate proportion of successful retrievals vs. a theoretical baseline
    derived from the number of agents.
    """
    # Handle list inputs by aggregating
    if isinstance(successful, list):
        successful = sum(successful)
    elif successful is None:
        successful = 0
        
    if isinstance(total, list):
        total = sum(total) if total else 0
    elif total is None:
        total = successful  # If total is not provided, assume all successful were queried
        
    if isinstance(agents, list):
        agents = sum(agents) // len(agents) if agents else 1

    # Validate inputs
    if successful < 0:
        raise ValueError("Successful retrievals cannot be negative")
    if agents <= 0:
        raise ValueError("Number of agents must be positive")

    # If total is 0, efficiency is 0 if no successful retrievals, else undefined (treat as 1.0)
    if total == 0:
        efficiency = 1.0 if successful > 0 else 0.0
    else:
        efficiency = successful / total

    # Clamp to [0, 1]
    efficiency = max(0.0, min(1.0, efficiency))

    # Theoretical baseline: In a full network, efficiency should be high.
    # A simple baseline model: 1 - (1 / agents) represents the probability of
    # finding a fact in a distributed system of 'agents' nodes.
    if agents > 1:
        theoretical_baseline = 1.0 - (1.0 / agents)
    else:
        theoretical_baseline = 1.0

    # Error rate relative to baseline
    error_rate = max(0.0, theoretical_baseline - efficiency)

    metrics = RetrievalMetrics(
        efficiency=efficiency,
        successful_retrievals=successful,
        total_queries=total,
        agents=agents,
        theoretical_baseline=theoretical_baseline,
        error_rate=error_rate
    )

    return efficiency, metrics


def validate_retrieval_efficiency(efficiency: float) -> bool:
    """Validate that efficiency is within expected bounds [0, 1]."""
    return 0.0 <= efficiency <= 1.0


def batch_compute_retrieval_efficiency(
    results: List[Dict[str, Any]]
) -> Tuple[float, RetrievalMetrics]:
    """
    Compute aggregate retrieval efficiency from a list of game results.

    Args:
        results: List of dicts containing 'successful_retrievals', 'total_queries', 'agents'.

    Returns:
        Tuple of (aggregate_efficiency, aggregate_metrics).
    """
    total_successful = 0
    total_queries = 0
    total_agents = 0
    count = 0

    for r in results:
        total_successful += r.get("successful_retrievals", 0)
        total_queries += r.get("total_queries", 0)
        total_agents += r.get("agents", 1)
        count += 1

    if count == 0:
        return 0.0, RetrievalMetrics(
            efficiency=0.0,
            successful_retrievals=0,
            total_queries=0,
            agents=0,
            theoretical_baseline=1.0
        )

    avg_agents = total_agents // count if count > 0 else 1

    return compute_retrieval_efficiency(total_successful, total_queries, avg_agents)