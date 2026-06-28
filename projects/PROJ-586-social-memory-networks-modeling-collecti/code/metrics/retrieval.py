"""
Cue-retrieval efficiency computation for social memory networks.

This module computes the retrieval efficiency metric measuring
how effectively agents retrieve information from the shared memory.
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

@dataclass
class RetrievalMetrics:
    """Metrics for retrieval analysis."""
    retrieval_rate: float
    retrieval_efficiency: float
    total_retrievals: int
    successful_retrievals: int

def compute_retrieval_rate(
    retrievals: List[Dict[str, Any]]
) -> float:
    """
    Compute the retrieval rate from a list of retrieval attempts.
    
    Args:
        retrievals: List of retrieval attempt records
    
    Returns:
        Retrieval rate (0 to 1)
    """
    if not retrievals:
        return 0.0
    
    successful = sum(1 for r in retrievals if r.get("retrieved", False))
    return successful / len(retrievals)

def compute_retrieval_efficiency(
    retrievals: List[Dict[str, Any]],
    num_agents: int
) -> float:
    """
    Compute retrieval efficiency compared to baseline.
    
    The retrieval efficiency measures how much better the retrieval rate
    is compared to random baseline (1/N_agents).
    
    Args:
        retrievals: List of retrieval attempt records
        num_agents: Number of agents in the network
    
    Returns:
        Retrieval efficiency (ratio vs. baseline)
    """
    if num_agents <= 0:
        return 0.0
    
    if not retrievals:
        return 0.0
    
    # Compute actual retrieval rate
    retrieval_rate = compute_retrieval_rate(retrievals)
    
    # Compute baseline (random retrieval probability)
    baseline = 1.0 / num_agents
    
    if baseline == 0:
        return 0.0
    
    # Efficiency = actual / baseline
    # > 1 means better than random, < 1 means worse
    efficiency = retrieval_rate / baseline
    
    return efficiency

def validate_retrieval_efficiency(
    efficiency: float,
    tolerance: float = 1e-6
) -> bool:
    """
    Validate that retrieval efficiency is in valid range.
    
    Args:
        efficiency: Computed retrieval efficiency
        tolerance: Numerical tolerance
    
    Returns:
        True if efficiency is valid
    """
    # Efficiency should be non-negative
    return efficiency >= -tolerance

def compute_game_level_retrieval(
    game_id: int,
    retrievals: List[Dict[str, Any]],
    num_agents: int
) -> Tuple[int, float]:
    """
    Compute retrieval efficiency for a single game.
    
    Args:
        game_id: Game identifier
        retrievals: Retrieval attempts for this game
        num_agents: Number of agents
    
    Returns:
        Tuple of (game_id, retrieval_efficiency)
    """
    efficiency = compute_retrieval_efficiency(retrievals, num_agents)
    return game_id, efficiency

if __name__ == "__main__":
    # Test computation
    test_retrievals = [
        {"agent_id": 0, "retrieved": True},
        {"agent_id": 1, "retrieved": True},
        {"agent_id": 0, "retrieved": False},
        {"agent_id": 2, "retrieved": True},
    ]
    
    rate = compute_retrieval_rate(test_retrievals)
    efficiency = compute_retrieval_efficiency(test_retrievals, 3)
    
    print(f"Retrieval rate: {rate:.4f}")
    print(f"Retrieval efficiency: {efficiency:.4f}")
    print(f"Valid: {validate_retrieval_efficiency(efficiency)}")
