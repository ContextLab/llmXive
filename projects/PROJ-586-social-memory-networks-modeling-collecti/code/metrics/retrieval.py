"""
Cue-Retrieval Efficiency Computation Module.

Implements the retrieval efficiency metric as defined in FR-005.
Calculates the proportion of successful retrievals vs. a theoretical baseline.
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np

@dataclass
class RetrievalMetrics:
    """Container for retrieval-related metrics."""
    efficiency: float
    success_rate: float
    baseline_rate: float
    total_queries: int
    successful_queries: int

def compute_retrieval_efficiency(
    successful: Union[int, float, List[int], List[float]], 
    total_queries: Union[int, float, List[int], List[float]], 
    agents: Union[int, float, List[int], List[float]]
) -> Tuple[float, RetrievalMetrics]:
    """
    Compute retrieval efficiency.
    
    This function is designed to be tolerant of various input shapes as per
    the cumulative call sites identified in the project.
    
    Args:
        successful: Number of successful retrievals (or list of successes per agent).
        total_queries: Total number of queries made (or list of queries per agent).
        agents: Number of agents (or list of agent IDs/counts).
        
    Returns:
        Tuple of (efficiency, RetrievalMetrics)
    """
    # Normalize inputs to scalars if lists are passed
    if isinstance(successful, list):
        successful = sum(successful)
    if isinstance(total_queries, list):
        total_queries = sum(total_queries)
    if isinstance(agents, list):
        agents = len(agents)
        
    # Ensure we are working with floats for division
    successful = float(successful)
    total_queries = float(total_queries)
    agents = int(agents)
    
    # Handle edge cases for division
    if total_queries <= 0:
        success_rate = 0.0
    else:
        success_rate = successful / total_queries
        
    # Theoretical baseline:
    # FR-005: "proportion of successful retrievals vs. a theoretical baseline derived from the number of agents"
    # Baseline for random guessing in a distributed system: 1/N_agents.
    if agents <= 0:
        baseline_rate = 1.0
    else:
        baseline_rate = 1.0 / agents
    
    # Calculate efficiency as normalized improvement over baseline
    # Formula: (Observed - Baseline) / (1 - Baseline)
    # This normalizes the score such that:
    # - Random guessing yields 0.0
    # - Perfect retrieval yields 1.0
    if baseline_rate < 1.0:
        efficiency = (success_rate - baseline_rate) / (1.0 - baseline_rate)
        # Clamp to [0, 1] range to handle cases where success_rate < baseline_rate
        efficiency = max(0.0, min(1.0, efficiency))
    else:
        # If baseline is 1.0 (single agent scenario), efficiency equals success rate
        efficiency = success_rate

    metrics = RetrievalMetrics(
        efficiency=float(efficiency),
        success_rate=float(success_rate),
        baseline_rate=float(baseline_rate),
        total_queries=int(total_queries),
        successful_queries=int(successful)
    )
    
    return float(efficiency), metrics

def validate_retrieval_efficiency(efficiency: float) -> bool:
    """Validate that retrieval efficiency is within [0, 1]."""
    return 0.0 <= efficiency <= 1.0

def batch_compute_retrieval_efficiency(game_results: List[Dict[str, Any]]) -> List[RetrievalMetrics]:
    """Compute retrieval efficiency for a batch of game results."""
    results = []
    for game in game_results:
        successful = game.get("successful_retrievals", 0)
        total = game.get("total_queries", 0)
        agents = game.get("num_agents", 1)
        eff, metrics = compute_retrieval_efficiency(successful, total, agents)
        results.append(metrics)
    return results