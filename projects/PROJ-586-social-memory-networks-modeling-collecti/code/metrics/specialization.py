"""Specialization metrics computation.

Implements FR-004: Calculate distribution-based metric of per-agent fact contribution,
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
    """Container for specialization-related metrics."""
    gini: float = 0.0
    entropy: float = 0.0
    specialization_index: float = 0.0
    max_entropy: float = 0.0
    raw_entropy: float = 0.0


def compute_gini_coefficient(values: List[float]) -> float:
    """Compute Gini coefficient for a list of values.

    The Gini coefficient measures inequality in the distribution.
    0 = perfect equality, 1 = perfect inequality.
    """
    if not values or sum(values) == 0:
        return 0.0
    sorted_values = sorted(values)
    n = len(sorted_values)
    cumsum = np.cumsum(sorted_values)
    total_sum = cumsum[-1]
    if total_sum == 0:
        return 0.0
    # Gini formula: (n + 1 - 2 * sum(cumsum) / total_sum) / n
    return (n + 1 - 2 * np.sum(cumsum) / total_sum) / n


def compute_shannon_entropy(values: List[float]) -> float:
    """Compute Shannon entropy for a list of values.

    Entropy measures the uncertainty/diversity in the distribution.
    Max entropy for N agents is log(N) (natural log).
    """
    total = sum(values)
    if total == 0:
        return 0.0
    probs = [v / total for v in values if v > 0]
    if not probs:
        return 0.0
    # Shannon entropy: -sum(p * ln(p))
    return -sum(p * math.log(p) for p in probs)


def compute_specialization_index(
    agent_skills: Union[List[int], List[float], Dict[str, Any], Any, None] = None,
    num_agents: Optional[int] = None,
    **kwargs
) -> Tuple[float, SpecializationMetrics]:
    """Compute the specialization index based on the distribution of facts/skills.

    Per FR-004: Calculate distribution-based metric of per-agent fact contribution,
    bounded 0 to log2(N_agents).

    The specialization index is computed as:
    - Raw entropy: Shannon entropy of the fact distribution across agents
    - Max entropy: log2(N_agents) - the theoretical maximum if facts were uniformly distributed
    - Specialization Index: Max_entropy - Raw_entropy

    This yields a value in [0, log2(N_agents)] where:
    - 0 indicates perfect equality (all agents hold equal facts)
    - log2(N_agents) indicates perfect specialization (one agent holds all facts)

    Handles multiple call signatures for compatibility:
    1. compute_specialization_index([list_of_counts], num_agents=N)
    2. compute_specialization_index(game_result_dict)
    3. compute_specialization_index(num_agents=N) -> returns uniform distribution index
    4. compute_specialization_index(agents=..., num_agents=...)
    5. compute_specialization_index(num_facts, num_agents) -> uniform distribution

    Args:
        agent_skills: Can be:
            - List of fact counts per agent
            - Dict containing 'facts_per_agent' or 'agent_skills'
            - Single int/float (treated as num_agents for uniform dist, or num_facts)
            - None (requires num_agents to be provided)
        num_agents: Number of agents (required if agent_skills is None or not a list)
        **kwargs: Additional parameters for compatibility

    Returns:
        Tuple of (specialization_index, SpecializationMetrics) where:
            - specialization_index is in [0, log2(N_agents)]
            - metrics contains gini, entropy, and other diagnostic values
    """
    # Handle various input shapes
    if agent_skills is None:
        # Case: called with only num_agents or kwargs
        if num_agents is None:
            num_agents = kwargs.get("num_agents", 0)
        if num_agents is None or num_agents <= 0:
            return 0.0, SpecializationMetrics()
        # Uniform distribution: all agents have 1 fact
        agent_skills = [1] * num_agents

    # Handle dict input (game result)
    if isinstance(agent_skills, dict):
        # Try to extract facts_per_agent
        if "facts_per_agent" in agent_skills:
            agent_skills = agent_skills["facts_per_agent"]
        elif "agent_skills" in agent_skills:
            agent_skills = agent_skills["agent_skills"]
        else:
            # Fallback: try to find any list-like value
            for key in agent_skills:
                if isinstance(agent_skills[key], (list, np.ndarray)):
                    agent_skills = agent_skills[key]
                    break
            else:
                return 0.0, SpecializationMetrics()

    # Normalize input to list of numbers
    if isinstance(agent_skills, (int, float)):
        # Legacy: treat as count, generate dummy distribution (uniform)
        n = int(agent_skills)
        if n <= 0:
            return 0.0, SpecializationMetrics()
        # If num_agents is provided, use it; otherwise assume n agents with 1 fact each
        if num_agents is None:
            num_agents = n
            agent_skills = [1] * num_agents
        else:
            # Treat as total facts distributed uniformly
            agent_skills = [n / num_agents] * num_agents
    elif isinstance(agent_skills, np.ndarray):
        agent_skills = agent_skills.tolist()

    if not isinstance(agent_skills, list):
        try:
            agent_skills = list(agent_skills)
        except (TypeError, ValueError):
            return 0.0, SpecializationMetrics()

    if not agent_skills:
        return 0.0, SpecializationMetrics()

    # Determine num_agents
    if num_agents is None:
        num_agents = len(agent_skills)

    # Ensure list length matches num_agents if provided
    if len(agent_skills) != num_agents:
        if len(agent_skills) < num_agents:
            agent_skills = list(agent_skills) + [0] * (num_agents - len(agent_skills))
        else:
            agent_skills = agent_skills[:num_agents]

    # Convert to float for computation
    agent_skills = [float(v) for v in agent_skills]

    # Compute metrics
    gini = compute_gini_coefficient(agent_skills)
    raw_entropy = compute_shannon_entropy(agent_skills)

    # Max entropy: log2(N_agents) per FR-004 requirement
    # This is the entropy of a uniform distribution over N agents
    if num_agents > 1:
        max_entropy = math.log2(num_agents)
    else:
        max_entropy = 0.0  # Single agent: no distribution, entropy is 0

    # Specialization Index: max_entropy - raw_entropy
    # This gives us a value in [0, log2(N_agents)]
    # - 0 when distribution is uniform (max entropy)
    # - log2(N_agents) when one agent has all facts (zero entropy)
    specialization_index = max_entropy - raw_entropy

    # Ensure non-negative (should always be true by construction)
    specialization_index = max(0.0, specialization_index)

    metrics = SpecializationMetrics(
        gini=gini,
        entropy=raw_entropy,
        specialization_index=specialization_index,
        max_entropy=max_entropy,
        raw_entropy=raw_entropy
    )

    return specialization_index, metrics


def validate_specialization_index(index: float, num_agents: Optional[int] = None) -> bool:
    """Validate that the index is in [0, log2(N_agents)].

    Args:
        index: The specialization index value
        num_agents: Number of agents (optional, if provided checks against log2(N))

    Returns:
        True if index is in valid range, False otherwise
    """
    if index < 0.0:
        return False
    if num_agents is not None and num_agents > 1:
        max_allowed = math.log2(num_agents)
        return index <= max_allowed + 1e-9  # Allow small floating point error
    return True


def batch_compute_specialization(results: List[Dict[str, Any]]) -> List[float]:
    """Compute specialization index for a list of game results.

    Args:
        results: List of game result dictionaries, each containing 'facts_per_agent'

    Returns:
        List of specialization indices, one per game
    """
    indices = []
    for res in results:
        # Assume 'facts_per_agent' is in the result
        if "facts_per_agent" in res:
            idx, _ = compute_specialization_index(res["facts_per_agent"])
            indices.append(idx)
        elif "agent_skills" in res:
            idx, _ = compute_specialization_index(res["agent_skills"])
            indices.append(idx)
        else:
            indices.append(0.0)
    return indices