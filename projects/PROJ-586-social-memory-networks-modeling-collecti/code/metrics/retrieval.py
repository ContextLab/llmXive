import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

@dataclass
class RetrievalMetrics:
    """Metrics for retrieval efficiency."""
    retrieval_efficiency: float
    success_rate: float
    baseline: float

def compute_retrieval_rate(successes: List[int], total_attempts: int) -> float:
    """
    Compute raw retrieval success rate.
    
    Args:
        successes: List of 1 (success) or 0 (failure)
        total_attempts: Total number of attempts
        
    Returns:
        Success rate (0.0 to 1.0)
    """
    if total_attempts == 0:
        return 0.0
    return sum(successes) / total_attempts

def compute_retrieval_efficiency(successes: List[int], agent_count: int) -> float:
    """
    Compute retrieval efficiency relative to random baseline.
    
    The baseline is 1/N_agents (random guessing).
    Efficiency = (actual_rate - baseline) / (1 - baseline)
    Range: 0 (baseline) to 1 (perfect)
    
    Args:
        successes: List of 1 (success) or 0 (failure)
        agent_count: Number of agents
        
    Returns:
        Retrieval efficiency (0.0 to 1.0)
    """
    if not successes:
        return 0.0
    
    total = len(successes)
    actual_rate = sum(successes) / total
    baseline = 1.0 / agent_count if agent_count > 0 else 0.0
    
    if baseline >= 1.0:
        return 1.0 if actual_rate >= baseline else 0.0
    
    # Normalize relative to baseline
    # If actual == baseline, efficiency = 0
    # If actual == 1.0, efficiency = 1
    if actual_rate <= baseline:
        return 0.0
    
    efficiency = (actual_rate - baseline) / (1.0 - baseline)
    return max(0.0, min(1.0, efficiency))

def validate_retrieval_efficiency(efficiency: float) -> bool:
    """
    Validate retrieval efficiency is in valid range.
    
    Args:
        efficiency: The computed efficiency
        
    Returns:
        True if valid
    """
    return 0.0 <= efficiency <= 1.0

def compute_game_level_retrieval(game_data: Dict[str, Any]) -> RetrievalMetrics:
    """
    Compute retrieval metrics for a single game.
    
    Args:
        game_data: Dictionary containing game state
        
    Returns:
        RetrievalMetrics object
    """
    turns = game_data.get('turns', [])
    successes = [1 if t.get('success') else 0 for t in turns if t.get('action') == 'retrieve']
    total_retrievals = len([t for t in turns if t.get('action') == 'retrieve'])
    
    success_rate = compute_retrieval_rate(successes, total_retrievals)
    agent_count = game_data.get('config', {}).get('num_agents', 1)
    efficiency = compute_retrieval_efficiency(successes, agent_count)
    baseline = 1.0 / agent_count if agent_count > 0 else 0.0
    
    return RetrievalMetrics(
        retrieval_efficiency=efficiency,
        success_rate=success_rate,
        baseline=baseline
    )
