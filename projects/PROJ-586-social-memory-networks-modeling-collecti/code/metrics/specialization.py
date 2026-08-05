"""Specialization index computation for social memory networks."""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np


@dataclass
class SpecializationMetrics:
    """Metrics for specialization computation."""
    specialization_index: float
    entropy: float
    gini_coefficient: float
    distribution: Dict[int, int] = field(default_factory=dict)


def compute_gini_coefficient(values: List[float]) -> float:
    """Compute Gini coefficient for a list of values.
    
    Args:
        values: List of numerical values
        
    Returns:
        Gini coefficient between 0 and 1
    """
    if not values or len(values) == 0:
        return 0.0
    
    values = np.array(values)
    if np.sum(values) == 0:
        return 0.0
    
    sorted_values = np.sort(values)
    n = len(values)
    index = np.arange(1, n + 1)
    gini = (2 * np.sum(index * sorted_values) - (n + 1) * np.sum(sorted_values)) / (n * np.sum(sorted_values))
    return max(0.0, min(1.0, gini))


def compute_shannon_entropy(counts: List[int]) -> float:
    """Compute Shannon entropy for a list of counts.
    
    Args:
        counts: List of counts for each category
        
    Returns:
        Shannon entropy value
    """
    if not counts or sum(counts) == 0:
        return 0.0
    
    total = sum(counts)
    probabilities = [c / total for c in counts if c > 0]
    
    entropy = 0.0
    for p in probabilities:
        if p > 0:
            entropy -= p * math.log2(p)
    
    return entropy


def compute_specialization_index(
    agent_facts: Union[List[List[str]], Dict[int, List[str]], None],
    num_agents: Optional[int] = None
) -> Tuple[float, SpecializationMetrics]:
    """
    Compute the specialization index for a set of agents.
    
    The specialization index measures how evenly facts are distributed across agents.
    A value of 0 indicates perfect specialization (each agent has unique facts),
    while higher values indicate more overlap.
    
    Args:
        agent_facts: List of fact lists per agent, or dict mapping agent_id to facts
        num_agents: Number of agents (optional, inferred if not provided)
        
    Returns:
        Tuple of (specialization_index, metrics_object)
    """
    # Handle different input types
    if agent_facts is None:
        agent_facts = []
    
    if isinstance(agent_facts, dict):
        if num_agents is None:
            num_agents = len(agent_facts)
        facts_list = [agent_facts.get(i, []) for i in range(num_agents)]
    elif isinstance(agent_facts, list):
        facts_list = agent_facts
        if num_agents is None:
            num_agents = len(facts_list)
    else:
        # Fallback for unexpected types
        facts_list = []
        num_agents = num_agents or 0
    
    if num_agents == 0:
        return 0.0, SpecializationMetrics(
            specialization_index=0.0,
            entropy=0.0,
            gini_coefficient=0.0,
            distribution={}
        )
    
    # Count facts per agent
    fact_counts = [len(facts) for facts in facts_list]
    
    # Compute distribution
    distribution = {i: count for i, count in enumerate(fact_counts)}
    
    # Compute entropy
    entropy = compute_shannon_entropy(fact_counts)
    
    # Compute Gini coefficient
    gini = compute_gini_coefficient([float(c) for c in fact_counts])
    
    # Specialization index: bounded 0 to log2(N_agents)
    # Higher values indicate more specialization
    max_entropy = math.log2(num_agents) if num_agents > 1 else 1.0
    specialization_index = entropy / max_entropy if max_entropy > 0 else 0.0
    
    # Ensure bounds
    specialization_index = max(0.0, min(math.log2(num_agents) if num_agents > 1 else 1.0, specialization_index))
    
    metrics = SpecializationMetrics(
        specialization_index=specialization_index,
        entropy=entropy,
        gini_coefficient=gini,
        distribution=distribution
    )
    
    return specialization_index, metrics


def validate_specialization_index(index: float, num_agents: int) -> bool:
    """Validate that specialization index is within expected bounds.
    
    Args:
        index: Computed specialization index
        num_agents: Number of agents
        
    Returns:
        True if valid, False otherwise
    """
    if num_agents <= 0:
        return False
    
    max_value = math.log2(num_agents) if num_agents > 1 else 1.0
    return 0.0 <= index <= max_value


def batch_compute_specialization(
    games_data: List[Dict[str, Any]],
    num_agents: int
) -> List[SpecializationMetrics]:
    """Compute specialization metrics for multiple games.
    
    Args:
        games_data: List of game data dictionaries
        num_agents: Number of agents per game
        
    Returns:
        List of SpecializationMetrics objects
    """
    results = []
    for game_data in games_data:
        agent_facts = game_data.get("agent_facts", [])
        index, metrics = compute_specialization_index(agent_facts, num_agents)
        results.append(metrics)
    return results


def compute_specialization_index_v1(
    agent_skills: Dict[int, List[str]],
    num_agents: Optional[int] = None
) -> Tuple[float, SpecializationMetrics]:
    """Legacy alias for compute_specialization_index (v1 compatibility)."""
    return compute_specialization_index(agent_skills, num_agents)
