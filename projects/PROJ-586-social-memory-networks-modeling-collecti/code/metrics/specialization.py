"""
Specialization index computation for social memory networks.

This module computes the specialization index (0 to log₂(N_agents))
measuring how specialized agents are in their memory contributions.
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import math

@dataclass
class SpecializationMetrics:
    """Metrics for agent specialization analysis."""
    specialization_index: float
    per_agent_specialization: List[float]
    max_specialization: float
    normalized_index: float

def compute_specialization_index(
    memory_actions: List[Dict[str, Any]],
    num_agents: int
) -> float:
    """
    Compute the specialization index for a set of memory actions.
    
    The specialization index measures how specialized agents are in their
    memory contributions, ranging from 0 (no specialization) to log₂(N_agents)
    (perfect specialization).
    
    Args:
        memory_actions: List of memory action records
        num_agents: Number of agents in the network
    
    Returns:
        Specialization index value
    """
    if num_agents <= 1:
        return 0.0
    
    if not memory_actions:
        return 0.0
    
    # Count actions per agent
    agent_action_counts = defaultdict(int)
    for action in memory_actions:
        agent_id = action.get("agent_id", 0)
        agent_action_counts[agent_id] += 1
    
    # Compute specialization using entropy-based formula
    total_actions = sum(agent_action_counts.values())
    if total_actions == 0:
        return 0.0
    
    # Calculate entropy of action distribution
    entropy = 0.0
    for agent_id in range(num_agents):
        count = agent_action_counts.get(agent_id, 0)
        if count > 0:
            p = count / total_actions
            entropy -= p * np.log2(p)
    
    # Max entropy (uniform distribution) is log2(num_agents)
    max_entropy = np.log2(num_agents)
    
    # Specialization = max_entropy - entropy
    # When all actions from one agent: entropy=0, specialization=max_entropy
    # When uniform: entropy=max_entropy, specialization=0
    specialization = max_entropy - entropy
    
    return specialization

def compute_game_level_specialization(
    game_id: int,
    memory_actions: List[Dict[str, Any]],
    num_agents: int
) -> Tuple[int, float]:
    """
    Compute specialization index for a single game.
    
    Args:
        game_id: Game identifier
        memory_actions: Memory actions for this game
        num_agents: Number of agents
    
    Returns:
        Tuple of (game_id, specialization_index)
    """
    specialization = compute_specialization_index(memory_actions, num_agents)
    return game_id, specialization

def validate_specialization_index(
    specialization: float,
    num_agents: int,
    tolerance: float = 1e-6
) -> bool:
    """
    Validate that specialization index is in valid range.
    
    Args:
        specialization: Computed specialization index
        num_agents: Number of agents
        tolerance: Numerical tolerance for boundary checks
    
    Returns:
        True if specialization is valid
    """
    if num_agents <= 1:
        return abs(specialization) < tolerance
    
    max_specialization = np.log2(num_agents)
    return -tolerance <= specialization <= max_specialization + tolerance

if __name__ == "__main__":
    # Test computation
    test_actions = [
        {"agent_id": 0, "action": "store"},
        {"agent_id": 0, "action": "store"},
        {"agent_id": 1, "action": "retrieve"},
        {"agent_id": 2, "action": "store"},
    ]
    
    spec = compute_specialization_index(test_actions, 3)
    print(f"Specialization index: {spec:.4f}")
    print(f"Valid: {validate_specialization_index(spec, 3)}")
