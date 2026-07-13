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
    baseline_efficiency: float = 0.0
    relative_improvement: float = 0.0


def compute_retrieval_efficiency(
    retrieved: Union[int, float, List[int], List[Dict[str, Any]]], 
    total: Optional[Union[int, float, List[int]]] = None, 
    agent_count: Optional[Union[int, List[int]]] = None
) -> Tuple[float, RetrievalMetrics]:
    """
    Compute retrieval efficiency based on successful retrievals vs theoretical baseline.
    
    Handles multiple call signatures for flexibility across different game simulation contexts:
    
    Signature 1: (retrieved, total, agent_count)
        - retrieved: int or float, number of successful retrievals
        - total: int or float, total number of retrieval attempts/queries
        - agent_count: int or list of ints, number of agents in the system
    
    Signature 2: (retrieved_list)
        - retrieved: list of dicts or ints, where each element represents a game's retrieval data
        - total and agent_count are extracted from each element if available
    
    Signature 3: (retrieved, total, [agent_list])
        - agent_count is a list, length is used as the agent count
    
    The efficiency is calculated as:
        efficiency = (successful_retrievals / total_queries) / theoretical_baseline
    
    Where theoretical_baseline is derived from the number of agents, representing
    the expected performance of a non-cooperative system.
    
    Returns:
        Tuple[float, RetrievalMetrics]: 
            - Normalized efficiency score (0.0 to 1.0 range typically)
            - Detailed metrics object with all computed values
    """
    # Handle list of game results (batch processing)
    if isinstance(retrieved, list):
        if len(retrieved) == 0:
            return 0.0, RetrievalMetrics()
        
        efficiencies = []
        total_retrieved = 0
        total_queries = 0
        agents_used = 1
        
        for item in retrieved:
            if isinstance(item, dict):
                r = item.get("retrieved", item.get("successful_retrievals", 0))
                t = item.get("total", item.get("total_queries", 1))
                a = item.get("agent_count", item.get("num_agents", 1))
            else:
                # Assume item is the retrieved count, need total and agents from elsewhere
                r = item
                t = total if total else 1
                a = agent_count if agent_count else 1
            
            if isinstance(a, list):
                a = len(a)
            
            eff, _ = compute_retrieval_efficiency(r, t, a)
            efficiencies.append(eff)
            total_retrieved += r
            total_queries += t
            agents_used = a if isinstance(a, int) else 1
        
        # Return average efficiency
        avg_eff = np.mean(efficiencies) if efficiencies else 0.0
        return avg_eff, RetrievalMetrics(
            efficiency=avg_eff,
            total_queries=total_queries,
            successful_retrievals=total_retrieved,
            baseline_efficiency=1.0 / agents_used if agents_used > 0 else 0.0
        )
    
    # Normalize inputs
    if isinstance(retrieved, list):
        retrieved = len(retrieved)
    
    if total is None:
        # If total is not provided, assume retrieved is the total and we have 0 failures
        # This handles cases where only successful retrievals are counted
        total = retrieved if retrieved > 0 else 1
        retrieved = total  # Assume 100% success if not specified
    
    if agent_count is None:
        agent_count = 1
    
    if isinstance(agent_count, list):
        n_agents = len(agent_count)
    else:
        n_agents = agent_count
    
    # Ensure non-negative values
    if n_agents <= 0:
        n_agents = 1
    if total <= 0:
        total = 1
    if retrieved < 0:
        retrieved = 0
    
    # Clamp retrieved to total
    if retrieved > total:
        retrieved = total
    
    # Calculate raw retrieval rate
    raw_rate = float(retrieved) / float(total)
    
    # Calculate theoretical baseline
    # In a non-cooperative system with N agents, the probability of any single
    # agent retrieving the correct information by chance is 1/N.
    # However, with memory sharing, we expect improvement over this baseline.
    theoretical_baseline = 1.0 / n_agents if n_agents > 0 else 1.0
    
    # Calculate efficiency relative to baseline
    # If raw_rate equals baseline, efficiency = 1.0
    # If raw_rate is better than baseline, efficiency > 1.0 (normalized to max 1.0 for report)
    if theoretical_baseline > 0:
        efficiency = raw_rate / theoretical_baseline
    else:
        efficiency = 1.0 if raw_rate > 0 else 0.0
    
    # Normalize to [0, 1] range for reporting, but keep raw efficiency for metrics
    normalized_efficiency = min(1.0, max(0.0, efficiency))
    
    # Calculate relative improvement over baseline
    relative_improvement = (raw_rate - theoretical_baseline) / theoretical_baseline if theoretical_baseline > 0 else 0.0
    
    metrics = RetrievalMetrics(
        efficiency=normalized_efficiency,
        total_queries=int(total),
        successful_retrievals=int(retrieved),
        baseline_efficiency=theoretical_baseline,
        relative_improvement=relative_improvement
    )
    
    return normalized_efficiency, metrics


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
        retrieved = res.get("successful_retrievals", res.get("num_queries", 0))
        total = res.get("total_queries", res.get("num_queries", 1))
        agents = res.get("agent_count", res.get("num_agents", 1))
        
        eff, _ = compute_retrieval_efficiency(retrieved, total, agents)
        efficiencies.append(eff)
    return efficiencies