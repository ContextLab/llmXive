"""
Cue-retrieval efficiency metrics for social memory experiments.

Computes retrieval rates and efficiency relative to random baseline.
"""
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class RetrievalMetrics:
    """Container for retrieval-related metrics."""
    retrieval_rate: float
    efficiency: float
    total_cues: int
    successful_retrievals: int
    baseline_rate: float


def compute_retrieval_rate(successful_retrievals: int, total_cues: int) -> float:
    """
    Compute the proportion of cues successfully retrieved.
    
    Args:
        successful_retrievals: Number of cues successfully retrieved.
        total_cues: Total number of cues presented.
        
    Returns:
        Retrieval rate as a float between 0 and 1.
    """
    if total_cues == 0:
        return 0.0
    return successful_retrievals / total_cues


def compute_retrieval_efficiency(retrieval_rate: float, num_agents: int) -> float:
    """
    Compute retrieval efficiency relative to random baseline.
    
    The baseline assumes random guessing with probability 1/N_agents.
    Efficiency = retrieval_rate / baseline_rate
    
    Args:
        retrieval_rate: The observed retrieval rate.
        num_agents: Number of agents in the system.
        
    Returns:
        Efficiency score (1.0 means matching random baseline, >1.0 means better).
    """
    if num_agents <= 0:
        return 0.0
    baseline_rate = 1.0 / num_agents
    if baseline_rate == 0:
        return 0.0
    return retrieval_rate / baseline_rate


def compute_game_level_retrieval(
    cues: List[str],
    retrieved_cues: List[str],
    num_agents: int
) -> Tuple[float, float]:
    """
    Compute retrieval metrics for a single game.
    
    Args:
        cues: List of all cues presented in the game.
        retrieved_cues: List of cues successfully retrieved by agents.
        num_agents: Number of agents in the system.
        
    Returns:
        Tuple of (retrieval_rate, efficiency).
    """
    total_cues = len(cues)
    successful_retrievals = len(retrieved_cues)
    
    retrieval_rate = compute_retrieval_rate(successful_retrievals, total_cues)
    efficiency = compute_retrieval_efficiency(retrieval_rate, num_agents)
    
    return retrieval_rate, efficiency


def validate_retrieval_efficiency(efficiency: float) -> bool:
    """
    Validate that retrieval efficiency is within expected bounds.
    
    Args:
        efficiency: The efficiency value to validate.
        
    Returns:
        True if efficiency is in [0, num_agents], False otherwise.
    """
    # Efficiency can theoretically be up to num_agents (if retrieval_rate=1.0)
    # In practice, we check it's non-negative and reasonable
    return 0.0 <= efficiency <= 100.0  # Cap at 100x baseline for sanity
