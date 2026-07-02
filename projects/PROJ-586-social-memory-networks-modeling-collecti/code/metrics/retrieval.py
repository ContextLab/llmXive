"""
Cue-retrieval efficiency computation for multi-agent systems.
Measures retrieval success relative to random baseline (1/N_agents).
"""
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

@dataclass
class RetrievalMetrics:
    """Container for retrieval metrics."""
    efficiency: float
    baseline: float
    success_rate: float

def compute_retrieval_efficiency(successful_retrievals: int, 
                                total_retrievals: int,
                                n_agents: int) -> RetrievalMetrics:
    """
    Compute retrieval efficiency metric.
    
    Efficiency = (successful / total) / (1 / N_agents)
    This measures how much better than random chance the agents perform.
    
    Args:
        successful_retrievals: Number of successful retrievals
        total_retrievals: Total number of retrieval attempts
        n_agents: Number of agents in the system
        
    Returns:
        RetrievalMetrics object
    """
    if total_retrievals == 0:
        return RetrievalMetrics(
            efficiency=0.0,
            baseline=1.0 / n_agents if n_agents > 0 else 0.0,
            success_rate=0.0
        )
    
    success_rate = successful_retrievals / total_retrievals
    baseline = 1.0 / n_agents if n_agents > 0 else 0.0
    
    if baseline == 0:
        efficiency = 0.0
    else:
        efficiency = success_rate / baseline
    
    # Clamp to reasonable range to avoid extreme outliers
    efficiency = min(max(efficiency, 0.0), 10.0)
    
    return RetrievalMetrics(
        efficiency=efficiency,
        baseline=baseline,
        success_rate=success_rate
    )

def compute_game_level_retrieval(game_data: Dict[str, Any]) -> float:
    """
    Compute retrieval efficiency for a single game.
    
    Args:
        game_data: Dictionary containing game results
        
    Returns:
        Retrieval efficiency value
    """
    successful = 0
    total = 0
    agent_ids = set()
    
    for action in game_data.get('actions', []):
        total += 1
        if action.get('success', False):
            successful += 1
        agent_ids.add(action.get('agent_id', ''))
    
    n_agents = len(agent_ids) if agent_ids else 1
    metrics = compute_retrieval_efficiency(successful, total, n_agents)
    return metrics.efficiency

def validate_retrieval_efficiency(value: float) -> Tuple[bool, str]:
    """
    Validate that a retrieval efficiency is within expected bounds.
    
    Args:
        value: The retrieval efficiency to validate
        
    Returns:
        Tuple of (is_valid, message)
    """
    # Efficiency should be non-negative and reasonably bounded
    # Typical range: 0 to ~5 (5x better than random)
    if value < -1e-6:
        return False, f"Value {value} is negative"
    if value > 10.0:
        return False, f"Value {value} seems abnormally high (>10)"
    return True, "Valid"
