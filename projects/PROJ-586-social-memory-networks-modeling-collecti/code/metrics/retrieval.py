"""
Retrieval efficiency computation for social memory networks.
"""
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

@dataclass
class RetrievalMetrics:
    """Container for retrieval metrics."""
    retrieval_efficiency: float
    total_attempts: int
    successful_retrievals: int
    is_valid: bool

def compute_retrieval_rate(
    retrieval_events: List[Dict[str, Any]]
) -> float:
    """
    Compute the raw retrieval rate (successes / attempts).
    
    Args:
        retrieval_events: List of retrieval event dictionaries
    
    Returns:
        Retrieval rate between 0 and 1
    """
    if not retrieval_events:
        return 0.0
    
    successful = sum(1 for event in retrieval_events if event.get("success", False))
    return successful / len(retrieval_events)

def compute_retrieval_efficiency(
    retrieval_events: List[Dict[str, Any]],
    num_agents: int
) -> RetrievalMetrics:
    """
    Compute retrieval efficiency relative to baseline.
    
    The baseline is 1/N_agents (random chance). Efficiency measures
    how much better the system performs compared to random guessing.
    
    Args:
        retrieval_events: List of retrieval event dictionaries
        num_agents: Number of agents in the system
    
    Returns:
        RetrievalMetrics object
    """
    if not retrieval_events:
        return RetrievalMetrics(0.0, 0, 0, True)
    
    total_attempts = len(retrieval_events)
    successful_retrievals = sum(1 for event in retrieval_events if event.get("success", False))
    
    # Compute raw success rate
    success_rate = successful_retrievals / total_attempts if total_attempts > 0 else 0.0
    
    # Compute baseline (random chance)
    baseline = 1.0 / num_agents if num_agents > 0 else 0.0
    
    # Efficiency: how many times better than baseline
    if baseline > 0:
        efficiency = success_rate / baseline
    else:
        efficiency = 0.0 if success_rate == 0.0 else 1.0
    
    # Normalize to 0-1 range for reporting
    # Maximum possible efficiency is num_agents (if everyone retrieves everything)
    max_efficiency = float(num_agents)
    normalized_efficiency = min(efficiency / max_efficiency, 1.0) if max_efficiency > 0 else 0.0
    
    is_valid = validate_retrieval_efficiency(normalized_efficiency, num_agents)
    
    return RetrievalMetrics(
        retrieval_efficiency=normalized_efficiency,
        total_attempts=total_attempts,
        successful_retrievals=successful_retrievals,
        is_valid=is_valid
    )

def validate_retrieval_efficiency(
    efficiency_value: float,
    num_agents: int
) -> bool:
    """
    Validate that retrieval efficiency is within expected bounds.
    
    Args:
        efficiency_value: Retrieval efficiency value
        num_agents: Number of agents
    
    Returns:
        True if valid, False otherwise
    """
    # Efficiency should be between 0 and 1
    return 0.0 <= efficiency_value <= 1.0

def compute_game_level_retrieval(
    game_results: Dict[str, Any],
    num_agents: int
) -> float:
    """
    Compute retrieval efficiency for a single game.
    
    Args:
        game_results: Results dictionary from run_single_game
        num_agents: Number of agents
    
    Returns:
        Retrieval efficiency value
    """
    retrieval_events = game_results.get("retrieval_events", [])
    metrics = compute_retrieval_efficiency(retrieval_events, num_agents)
    return metrics.retrieval_efficiency
