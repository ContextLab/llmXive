"""
Specialization index computation for multi-agent systems.
Measures how specialized agents are in their roles (0 to log2(N_agents)).
"""
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

@dataclass
class SpecializationMetrics:
    """Container for specialization metrics."""
    index: float
    max_possible: float
    normalized: float

def compute_specialization_index(agent_action_counts: List[int]) -> SpecializationMetrics:
    """
    Compute the specialization index based on action distribution.
    
    The specialization index is based on the entropy of the action distribution.
    Higher entropy = more equal distribution = less specialization.
    Lower entropy = more concentrated actions = more specialization.
    
    Args:
        agent_action_counts: List of action counts per agent
        
    Returns:
        SpecializationMetrics object
    """
    total_actions = sum(agent_action_counts)
    n_agents = len(agent_action_counts)
    
    if total_actions == 0 or n_agents == 0:
        return SpecializationMetrics(
            index=0.0,
            max_possible=0.0,
            normalized=0.0
        )
    
    # Compute probabilities
    probs = [count / total_actions for count in agent_action_counts]
    
    # Compute entropy: H = -sum(p * log2(p))
    entropy = 0.0
    for p in probs:
        if p > 0:
            entropy -= p * np.log2(p)
    
    # Maximum possible entropy is log2(N_agents)
    max_entropy = np.log2(n_agents) if n_agents > 1 else 1.0
    
    # Specialization is inversely related to entropy
    # We normalize to [0, 1] where 1 = perfectly specialized (one agent does all)
    # and 0 = perfectly distributed (all agents equal)
    normalized = 1.0 - (entropy / max_entropy) if max_entropy > 0 else 0.0
    
    return SpecializationMetrics(
        index=entropy,
        max_possible=max_entropy,
        normalized=normalized
    )

def compute_game_level_specialization(game_data: Dict[str, Any]) -> float:
    """
    Compute specialization index for a single game.
    
    Args:
        game_data: Dictionary containing game results with agent actions
        
    Returns:
        Normalized specialization index (0 to 1)
    """
    # Extract action counts per agent
    agent_counts = defaultdict(int)
    for action in game_data.get('actions', []):
        if action.get('success', False):
            agent_id = action.get('agent_id', 'agent_0')
            agent_idx = int(agent_id.split('_')[1]) if '_' in agent_id else 0
            agent_counts[agent_idx] += 1
    
    if not agent_counts:
        return 0.0
    
    # Convert to list (preserving order 0, 1, 2, ...)
    n_agents = max(agent_counts.keys()) + 1
    counts = [agent_counts.get(i, 0) for i in range(n_agents)]
    
    metrics = compute_specialization_index(counts)
    return metrics.normalized

def validate_specialization_index(value: float) -> Tuple[bool, str]:
    """
    Validate that a specialization index is within expected bounds.
    
    Args:
        value: The specialization index to validate
        
    Returns:
        Tuple of (is_valid, message)
    """
    # Normalized index should be in [0, 1]
    # Raw entropy should be in [0, log2(N)]
    if value < -1e-6 or value > 1.0 + 1e-6:
        return False, f"Value {value} outside expected range [0, 1]"
    return True, "Valid"
