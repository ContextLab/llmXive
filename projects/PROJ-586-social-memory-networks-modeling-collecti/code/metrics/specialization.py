import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import math

@dataclass
class SpecializationMetrics:
    """Metrics for agent specialization."""
    specialization_index: float
    entropy: float
    max_possible: float

def compute_specialization_index(knowledge_counts: List[int], agent_count: int) -> float:
    """
    Compute the specialization index for a group of agents.
    
    The specialization index measures how unevenly knowledge is distributed
    across agents. Higher values indicate more specialization.
    
    Formula: H_max - H_actual, where H is entropy
    Range: 0 (perfectly uniform) to log2(N_agents) (perfectly specialized)
    
    Args:
        knowledge_counts: List of knowledge item counts per agent
        agent_count: Total number of agents
        
    Returns:
        Specialization index value
    """
    if agent_count <= 0:
        return 0.0
    
    total_items = sum(knowledge_counts)
    if total_items == 0:
        return 0.0
    
    # Calculate probabilities
    probs = [k / total_items for k in knowledge_counts if k > 0]
    
    if not probs:
        return 0.0
    
    # Calculate entropy
    entropy = -sum(p * math.log2(p) for p in probs if p > 0)
    
    # Max entropy (uniform distribution)
    max_entropy = math.log2(agent_count)
    
    # Specialization index: difference from max
    spec_index = max_entropy - entropy
    
    # Clamp to valid range
    spec_index = max(0.0, min(spec_index, max_entropy))
    
    return spec_index

def compute_game_level_specialization(game_data: Dict[str, Any]) -> SpecializationMetrics:
    """
    Compute specialization metrics for a single game.
    
    Args:
        game_data: Dictionary containing game state
        
    Returns:
        SpecializationMetrics object
    """
    agent_knowledge = game_data.get('final_state', {}).get('agent_knowledge', {})
    knowledge_counts = [len(k) for k in agent_knowledge.values()]
    agent_count = len(knowledge_counts)
    
    spec_index = compute_specialization_index(knowledge_counts, agent_count)
    
    # Calculate entropy
    total = sum(knowledge_counts)
    if total > 0:
        probs = [k / total for k in knowledge_counts if k > 0]
        entropy = -sum(p * math.log2(p) for p in probs if p > 0)
    else:
        entropy = 0.0
    
    max_possible = math.log2(agent_count) if agent_count > 0 else 0.0
    
    return SpecializationMetrics(
        specialization_index=spec_index,
        entropy=entropy,
        max_possible=max_possible
    )

def validate_specialization_index(spec_index: float, agent_count: int) -> bool:
    """
    Validate that specialization index is within expected range.
    
    Args:
        spec_index: The computed specialization index
        agent_count: Number of agents
        
    Returns:
        True if valid, False otherwise
    """
    if agent_count <= 0:
        return True  # Edge case
    
    max_possible = math.log2(agent_count)
    return 0.0 <= spec_index <= max_possible + 1e-6  # Small tolerance for floating point
