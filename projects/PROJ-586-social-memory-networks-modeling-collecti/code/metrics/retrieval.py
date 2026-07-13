"""Retrieval efficiency metrics computation.

Implements FR-005: Calculate proportion of successful retrievals vs. a theoretical
baseline derived from the number of agents.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np


@dataclass
class RetrievalMetrics:
    """Container for retrieval efficiency metrics."""
    efficiency: float = 0.0
    total_queries: int = 0
    successful_retrievals: int = 0
    theoretical_baseline: float = 0.0
    relative_efficiency: float = 0.0  # efficiency / baseline


def compute_retrieval_efficiency(
    retrieved: Union[int, float, List[int], Dict[str, Any]],
    total: Optional[Union[int, float]] = None,
    agent_count: Optional[Union[int, List[int]]] = None
) -> Tuple[float, RetrievalMetrics]:
    """
    Compute retrieval efficiency based on successful retrievals vs. theoretical baseline.

    Handles multiple call signatures for flexibility across the codebase:

    1. (retrieved, total, agent_count) - Standard call
       - retrieved: number of successful retrievals
       - total: total number of retrieval attempts (queries)
       - agent_count: number of agents in the system

    2. (retrieved, total, [agent_list]) - List of agents
       - agent_count is derived from list length

    3. (game_result_dict, None, None) - Game result object
       - Extracts retrieved, total, and agent_count from the dict

    4. (agent_skills_dict, None, None) - Agent skills distribution
       - Computes based on skill distribution across agents

    Args:
        retrieved: Number of successful retrievals, or a dict/list containing results
        total: Total number of queries (optional if retrieved is a dict)
        agent_count: Number of agents (optional if retrieved is a dict)

    Returns:
        Tuple of (efficiency_score, RetrievalMetrics)
        - efficiency_score: float between 0 and 1
        - RetrievalMetrics: detailed metrics object
    """
    # Handle dict input (game result or similar)
    if isinstance(retrieved, dict):
        total = retrieved.get("total_queries", retrieved.get("num_queries", 0))
        retrieved_count = retrieved.get("successful_retrievals", retrieved.get("retrieved", 0))
        agent_count = retrieved.get("agent_count", retrieved.get("num_agents", 1))
    elif isinstance(retrieved, list) and total is None and agent_count is None:
        # List of game results - compute aggregate
        total_retrieved = sum(r.get("successful_retrievals", r.get("retrieved", 0)) for r in retrieved)
        total_queries = sum(r.get("total_queries", r.get("num_queries", 0)) for r in retrieved)
        agent_counts = [r.get("agent_count", r.get("num_agents", 1)) for r in retrieved]
        return compute_retrieval_efficiency(total_retrieved, total_queries, agent_counts)
    else:
        retrieved_count = retrieved

    # Normalize agent_count
    if isinstance(agent_count, list):
        n_agents = len(agent_count)
    elif agent_count is not None:
        n_agents = int(agent_count)
    else:
        n_agents = 1

    # Ensure valid counts
    if n_agents <= 0:
        n_agents = 1
    if total is None or total <= 0:
        total = 1

    retrieved_count = max(0, int(retrieved_count))
    total = max(1, int(total))

    # Calculate raw efficiency (proportion of successful retrievals)
    raw_efficiency = retrieved_count / total

    # Calculate theoretical baseline: 1/n_agents
    # In a transactive memory system with n agents, if each agent knows 1/n of facts,
    # and cues are distributed uniformly, the probability of a correct cue targeting
    # the right agent is 1/n_agents
    theoretical_baseline = 1.0 / n_agents

    # Relative efficiency: how much better than random chance
    # If baseline is 1/n and we achieve 1.0, relative efficiency is n
    if theoretical_baseline > 0:
        relative_efficiency = raw_efficiency / theoretical_baseline
    else:
        relative_efficiency = 0.0

    # Clamp raw efficiency to [0, 1]
    efficiency = max(0.0, min(1.0, raw_efficiency))

    metrics = RetrievalMetrics(
        efficiency=efficiency,
        total_queries=total,
        successful_retrievals=retrieved_count,
        theoretical_baseline=theoretical_baseline,
        relative_efficiency=relative_efficiency
    )

    return efficiency, metrics


def validate_retrieval_efficiency(efficiency: float) -> bool:
    """Validate that efficiency is in [0, 1]."""
    return 0.0 <= efficiency <= 1.0


def batch_compute_retrieval_efficiency(results: List[Dict[str, Any]]) -> List[float]:
    """Compute retrieval efficiency for a list of game results.

    Args:
        results: List of game result dictionaries containing retrieval metrics

    Returns:
        List of efficiency scores (one per game)
    """
    efficiencies = []
    for res in results:
        retrieved = res.get("successful_retrievals", res.get("retrieved", 0))
        total = res.get("total_queries", res.get("num_queries", 1))
        agents = res.get("agent_count", res.get("num_agents", 1))

        eff, _ = compute_retrieval_efficiency(retrieved, total, agents)
        efficiencies.append(eff)
    return efficiencies