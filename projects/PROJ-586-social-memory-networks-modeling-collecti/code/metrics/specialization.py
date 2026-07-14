"""
Specialization metrics for multi-agent memory networks.

Implements the specialization index as a distribution-based metric of per-agent
fact contribution, bounded between 0 and log2(N_agents).

FR-004: Calculate distribution-based metric of per-agent fact contribution,
bounded 0 to log2(N_agents).
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

@dataclass
class SpecializationMetrics:
    """Container for specialization computation results."""
    specialization_index: float
    entropy: float
    max_entropy: float
    gini_coefficient: Optional[float] = None
    facts_per_agent: Dict[int, int] = field(default_factory=dict)
    total_facts: int = 0
    num_agents: int = 0

def compute_gini_coefficient(values: List[float]) -> float:
    """
    Compute the Gini coefficient for a list of values.
    
    The Gini coefficient measures inequality in a distribution.
    0 = perfect equality, 1 = perfect inequality.
    
    Args:
        values: List of numeric values (e.g., facts per agent)
        
    Returns:
        Gini coefficient between 0 and 1
    """
    if not values or len(values) == 0:
        return 0.0
    
    values = np.array(values, dtype=float)
    if np.sum(values) == 0:
        return 0.0
    
    # Sort values
    sorted_values = np.sort(values)
    n = len(sorted_values)
    
    # Compute Gini using the formula: G = (2 * sum(i * x_i) - (n + 1) * sum(x_i)) / (n * sum(x_i))
    cumulative = np.cumsum(sorted_values)
    gini = (2.0 * np.sum((np.arange(1, n + 1) * sorted_values)) - (n + 1) * np.sum(sorted_values)) / (n * np.sum(sorted_values))
    
    return float(gini)

def compute_shannon_entropy(proportions: List[float]) -> float:
    """
    Compute Shannon entropy for a distribution of proportions.
    
    Args:
        proportions: List of proportions that sum to 1.0
        
    Returns:
        Shannon entropy (non-negative)
    """
    if not proportions or len(proportions) == 0:
        return 0.0
    
    # Filter out zero proportions to avoid log(0)
    filtered = [p for p in proportions if p > 0]
    
    if len(filtered) == 0:
        return 0.0
    
    entropy = -sum(p * math.log(p) for p in filtered)
    return entropy

def compute_specialization_index(
    facts_per_agent: Union[List[int], Dict[int, int], List[Dict[str, Any]], None],
    num_agents: Optional[int] = None
) -> Tuple[float, SpecializationMetrics]:
    """
    Compute the specialization index for a multi-agent system.
    
    The specialization index measures how unevenly facts are distributed across agents.
    - 0: Perfect equality (all agents contribute equally)
    - log2(N_agents): Maximum specialization (one agent contributes all facts)
    
    This is computed as: max_entropy - actual_entropy, where entropy is the
    Shannon entropy of the fact distribution across agents.
    
    Args:
        facts_per_agent: Can be:
            - List[int]: Direct list of fact counts per agent
            - Dict[int, int]: Mapping of agent_id -> fact_count
            - List[Dict]: List of game result dicts with 'agent_facts' or similar
            - None: Returns 0 with empty metrics
        num_agents: Total number of agents (optional, inferred if not provided)
        
    Returns:
        Tuple of (specialization_index, SpecializationMetrics)
        
    Raises:
        ValueError: If input is invalid or num_agents is inconsistent
    """
    # Handle None input
    if facts_per_agent is None:
        return 0.0, SpecializationMetrics(
            specialization_index=0.0,
            entropy=0.0,
            max_entropy=0.0,
            facts_per_agent={},
            total_facts=0,
            num_agents=num_agents or 0
        )
    
    # Parse input into a list of fact counts
    fact_counts: List[int] = []
    
    if isinstance(facts_per_agent, dict):
        fact_counts = list(facts_per_agent.values())
        if num_agents is None:
            num_agents = len(facts_per_agent)
    elif isinstance(facts_per_agent, list):
        if len(facts_per_agent) == 0:
            return 0.0, SpecializationMetrics(
                specialization_index=0.0,
                entropy=0.0,
                max_entropy=0.0,
                facts_per_agent={},
                total_facts=0,
                num_agents=num_agents or 0
            )
        
        # Check if it's a list of dicts (game results)
        if isinstance(facts_per_agent[0], dict):
            # Extract fact counts from game result format
            total_facts = 0
            agent_facts: Dict[int, int] = {}
            
            for item in facts_per_agent:
                if 'agent_facts' in item:
                    # Direct fact counts per agent
                    for agent_id, count in item['agent_facts'].items():
                        agent_facts[int(agent_id)] = int(count)
                        total_facts += int(count)
                elif 'facts_contributed' in item:
                    # Alternative format
                    for agent_id, count in item['facts_contributed'].items():
                        agent_facts[int(agent_id)] = int(count)
                        total_facts += int(count)
                elif 'agent_id' in item and 'fact_count' in item:
                    # Per-agent record format
                    agent_id = int(item['agent_id'])
                    count = int(item['fact_count'])
                    agent_facts[agent_id] = count
                    total_facts += count
            
            fact_counts = list(agent_facts.values())
            if num_agents is None:
                num_agents = len(agent_facts)
            if num_agents is None or num_agents == 0:
                num_agents = 1
        else:
            # Direct list of integers
            fact_counts = [int(x) for x in facts_per_agent]
            if num_agents is None:
                num_agents = len(fact_counts)
    else:
        # Try to convert to list
        try:
            fact_counts = [int(x) for x in facts_per_agent]
            if num_agents is None:
                num_agents = len(fact_counts)
        except (TypeError, ValueError):
            return 0.0, SpecializationMetrics(
                specialization_index=0.0,
                entropy=0.0,
                max_entropy=0.0,
                facts_per_agent={},
                total_facts=0,
                num_agents=num_agents or 0
            )
    
    # Ensure num_agents is valid
    if num_agents is None or num_agents <= 0:
        num_agents = max(1, len(fact_counts))
    
    # Pad fact_counts to num_agents if necessary
    while len(fact_counts) < num_agents:
        fact_counts.append(0)
    
    # Trim if too long
    fact_counts = fact_counts[:num_agents]
    
    total_facts = sum(fact_counts)
    
    if total_facts == 0:
        # No facts distributed
        return 0.0, SpecializationMetrics(
            specialization_index=0.0,
            entropy=0.0,
            max_entropy=math.log2(num_agents) if num_agents > 1 else 0.0,
            gini_coefficient=0.0,
            facts_per_agent={i: count for i, count in enumerate(fact_counts)},
            total_facts=0,
            num_agents=num_agents
        )
    
    # Compute proportions
    proportions = [count / total_facts for count in fact_counts]
    
    # Compute Shannon entropy
    actual_entropy = compute_shannon_entropy(proportions)
    
    # Maximum possible entropy (uniform distribution)
    max_entropy = math.log2(num_agents) if num_agents > 1 else 0.0
    
    # Specialization index: difference from maximum entropy
    # This measures how much the distribution deviates from uniform
    specialization_index = max_entropy - actual_entropy
    
    # Compute Gini coefficient as an additional metric
    gini = compute_gini_coefficient(fact_counts)
    
    # Ensure bounds: [0, log2(N_agents)]
    specialization_index = max(0.0, min(specialization_index, max_entropy))
    
    return specialization_index, SpecializationMetrics(
        specialization_index=specialization_index,
        entropy=actual_entropy,
        max_entropy=max_entropy,
        gini_coefficient=gini,
        facts_per_agent={i: count for i, count in enumerate(fact_counts)},
        total_facts=total_facts,
        num_agents=num_agents
    )

def validate_specialization_index(
    specialization_index: float,
    num_agents: int
) -> bool:
    """
    Validate that the specialization index is within expected bounds.
    
    Args:
        specialization_index: Computed specialization index
        num_agents: Number of agents in the system
        
    Returns:
        True if valid, False otherwise
    """
    if num_agents <= 0:
        return specialization_index == 0.0
    
    max_valid = math.log2(num_agents)
    return 0.0 <= specialization_index <= max_valid + 1e-9

def batch_compute_specialization(
    game_results: List[Dict[str, Any]],
    num_agents: int
) -> List[Tuple[float, SpecializationMetrics]]:
    """
    Compute specialization index for multiple game results.
    
    Args:
        game_results: List of game result dictionaries
        num_agents: Number of agents per game
        
    Returns:
        List of (specialization_index, metrics) tuples
    """
    results = []
    for game in game_results:
        idx, metrics = compute_specialization_index(
            facts_per_agent=game.get('agent_facts', game.get('facts_contributed', [])),
            num_agents=num_agents
        )
        results.append((idx, metrics))
    return results