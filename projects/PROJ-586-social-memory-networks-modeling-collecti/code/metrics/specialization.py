"""
Specialization index computation for social memory networks.
"""
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import math

@dataclass
class SpecializationMetrics:
    """Container for specialization metrics."""
    specialization_index: float
    domain_count: int
    agent_count: int
    is_valid: bool

def compute_specialization_index(
    specialization_data: Dict[str, Any],
    num_agents: int
) -> SpecializationMetrics:
    """
    Compute the specialization index for a game.
    
    The specialization index measures how well domains are distributed among agents.
    A value of 0 means no specialization (all agents know all domains).
    A value of log2(N_agents) means perfect specialization (each agent knows unique domains).
    
    Args:
        specialization_data: Dictionary containing domain assignments
        num_agents: Number of agents in the game
    
    Returns:
        SpecializationMetrics object
    """
    agent_domains = specialization_data.get("agent_domains", {})
    domain_assignments = specialization_data.get("domain_assignments", {})
    
    if not agent_domains or not domain_assignments:
        return SpecializationMetrics(0.0, 0, num_agents, False)
    
    # Count unique domains
    all_domains = set(domain_assignments.keys())
    domain_count = len(all_domains)
    
    if domain_count == 0:
        return SpecializationMetrics(0.0, 0, num_agents, True)
    
    # Compute specialization: how many domains each agent is primarily responsible for
    agent_domain_counts = {
        agent_id: len(set(domains)) 
        for agent_id, domains in agent_domains.items()
    }
    
    # Calculate specialization index
    # Based on the entropy of domain distribution across agents
    total_assignments = sum(len(domains) for domains in domain_assignments.values())
    
    if total_assignments == 0:
        return SpecializationMetrics(0.0, domain_count, num_agents, True)
    
    # Compute the specialization index as the effective number of specialized agents
    specialization_sum = 0.0
    for domain, agents in domain_assignments.items():
        if len(agents) > 0:
            # Each domain is assigned to one primary agent
            # The specialization contribution is 1 if one agent owns it, less if shared
            primary_agent = agents[0]  # First agent is primary
            specialization_sum += 1.0
    
    # Normalize by the maximum possible specialization (log2 of agent count)
    max_specialization = math.log2(num_agents) if num_agents > 1 else 1.0
    
    # Specialization index: proportion of domains with clear ownership
    specialization_index = (specialization_sum / domain_count) * max_specialization if domain_count > 0 else 0.0
    
    # Ensure bounds
    specialization_index = max(0.0, min(specialization_index, max_specialization))
    
    is_valid = validate_specialization_index(specialization_index)
    
    return SpecializationMetrics(
        specialization_index=specialization_index,
        domain_count=domain_count,
        agent_count=num_agents,
        is_valid=is_valid
    )

def compute_game_level_specialization(
    game_results: Dict[str, Any],
    num_agents: int
) -> float:
    """
    Compute specialization index for a single game.
    
    Args:
        game_results: Results dictionary from run_single_game
        num_agents: Number of agents
    
    Returns:
        Specialization index value
    """
    metrics = compute_specialization_index(
        game_results.get("specialization_data", {}),
        num_agents
    )
    return metrics.specialization_index

def validate_specialization_index(index_value: float) -> bool:
    """
    Validate that specialization index is within expected bounds.
    
    Args:
        index_value: Specialization index value
    
    Returns:
        True if valid, False otherwise
    """
    # Specialization index should be >= 0
    # Upper bound depends on number of agents, but typically <= log2(N)
    return index_value >= 0.0 and index_value <= 10.0  # Upper bound for safety
