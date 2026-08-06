"""Retrieval efficiency computation for social memory networks."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from utils.logging import get_logger


logger = get_logger(__name__)


@dataclass
class RetrievalMetrics:
    """Metrics for retrieval computation."""
    retrieval_efficiency: float
    success_rate: float
    total_queries: int
    successful_retrievals: int
    theoretical_baseline: float


def compute_retrieval_efficiency(
    successful_retrievals: Union[int, float],
    total_queries: Union[int, float],
    num_agents: Union[int, float, List[int]]
) -> Tuple[float, RetrievalMetrics]:
    """
    Compute retrieval efficiency for a set of queries.
    
    The retrieval efficiency measures the proportion of successful retrievals
    compared to a theoretical baseline derived from the number of agents.
    
    Args:
        successful_retrievals: Number of successful retrievals
        total_queries: Total number of queries made
        num_agents: Number of agents (int, float, or list)
        
    Returns:
        Tuple of (retrieval_efficiency, metrics_object)
    """
    # Handle different input types for num_agents
    if isinstance(num_agents, list):
        avg_agents = len(num_agents) if len(num_agents) > 0 else 1
    else:
        avg_agents = float(num_agents) if num_agents > 0 else 1.0
    
    # Ensure non-negative values
    successful = max(0, int(successful_retrievals))
    total = max(1, int(total_queries))  # Avoid division by zero
    
    # Compute success rate
    success_rate = successful / total if total > 0 else 0.0
    
    # Theoretical baseline: perfect retrieval across all agents
    # In a perfect system, efficiency would be 1.0
    # Baseline derived from agent count to reflect collective potential
    theoretical_baseline = 1.0
    
    # Retrieval efficiency: normalized success rate
    retrieval_efficiency = success_rate / theoretical_baseline if theoretical_baseline > 0 else 0.0
    
    # Ensure bounds [0, 1]
    retrieval_efficiency = max(0.0, min(1.0, retrieval_efficiency))
    
    metrics = RetrievalMetrics(
        retrieval_efficiency=retrieval_efficiency,
        success_rate=success_rate,
        total_queries=total,
        successful_retrievals=successful,
        theoretical_baseline=theoretical_baseline
    )
    
    # Validation logic
    if not validate_retrieval_efficiency(retrieval_efficiency, int(avg_agents)):
        logger.warning(
            f"Retrieval efficiency {retrieval_efficiency} out of bounds "
            f"for {int(avg_agents)} agents"
        )
    
    return retrieval_efficiency, metrics


def validate_retrieval_efficiency(
    efficiency: float,
    num_agents: int
) -> bool:
    """Validate that retrieval efficiency is within expected bounds.
    
    Args:
        efficiency: Computed retrieval efficiency
        num_agents: Number of agents
        
    Returns:
        True if valid, False otherwise
    """
    if num_agents <= 0:
        return False
    
    return 0.0 <= efficiency <= 1.0


def batch_compute_retrieval_efficiency(
    games_data: List[Dict[str, Any]]
) -> List[RetrievalMetrics]:
    """Compute retrieval metrics for multiple games.
    
    Args:
        games_data: List of game data dictionaries
        
    Returns:
        List of RetrievalMetrics objects
    """
    results = []
    for game_data in games_data:
        successful = game_data.get("successful_retrievals", 0)
        total = game_data.get("total_queries", 1)
        num_agents = game_data.get("num_agents", 1)
        
        efficiency, metrics = compute_retrieval_efficiency(successful, total, num_agents)
        results.append(metrics)
    return results