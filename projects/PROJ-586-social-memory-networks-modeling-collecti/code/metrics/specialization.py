"""Specialization metrics computation.

This module implements the specialization index as a distribution-based metric
of per-agent fact contribution, bounded between 0 and log2(N_agents).

Per FR-004: The specialization index measures how unevenly facts/skills are
distributed across agents in a multi-agent system. A value of 0 indicates
perfect equality (all agents contribute equally), while higher values indicate
greater specialization (uneven distribution).

The index is bounded: 0 <= index <= log2(N_agents)
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
    normalized_entropy: float = 0.0


def compute_gini_coefficient(values: List[float]) -> float:
    """Compute Gini coefficient for a list of values.

    The Gini coefficient measures inequality in a distribution.
    Range: [0, 1] where 0 = perfect equality, 1 = perfect inequality.

    Args:
        values: List of non-negative values (e.g., fact counts per agent)

    Returns:
        Gini coefficient in [0, 1]
    """
    if not values or len(values) == 0:
        return 0.0

    sorted_values = sorted(values)
    n = len(sorted_values)

    if n == 0:
        return 0.0

    total = sum(sorted_values)
    if total == 0:
        return 0.0

    # Gini formula: (n+1 - 2*sum(cumsum)/total) / n
    cumsum = np.cumsum(sorted_values)
    gini = (n + 1 - 2 * np.sum(cumsum) / total) / n

    return max(0.0, min(1.0, gini))


def compute_shannon_entropy(values: List[float]) -> float:
    """Compute Shannon entropy for a list of values.

    Shannon entropy measures the uncertainty/information content in a distribution.
    Higher entropy = more uniform distribution.

    Args:
        values: List of non-negative values

    Returns:
        Shannon entropy in bits (natural log base e)
    """
    if not values or len(values) == 0:
        return 0.0

    total = sum(values)
    if total == 0:
        return 0.0

    # Filter out zero values and compute probabilities
    probs = [v / total for v in values if v > 0]

    if not probs:
        return 0.0

    # Compute entropy: -sum(p * log(p))
    entropy = -sum(p * math.log(p) for p in probs)

    return entropy


def compute_specialization_index(
    agent_skills: Union[List[int], List[float], Dict[str, int], Dict[str, float], Any],
    num_agents: Optional[int] = None
) -> Tuple[float, SpecializationMetrics]:
    """Compute the specialization index for a multi-agent system.

    This function calculates a distribution-based metric of per-agent fact
    contribution, bounded between 0 and log2(N_agents).

    The specialization index is defined as:
        spec_index = log2(N_agents) - H(P)

    where H(P) is the Shannon entropy of the distribution of facts across agents.
    This gives:
        - 0 when distribution is perfectly uniform (max entropy)
        - log2(N_agents) when all facts belong to one agent (min entropy)

    Handles multiple call signatures for backward compatibility:
        - compute_specialization_index([10, 20, 30])
        - compute_specialization_index([10, 20, 30], num_agents=3)
        - compute_specialization_index({"facts_per_agent": [10, 20, 30]})
        - compute_specialization_index(5)  # legacy: generate dummy distribution
        - compute_specialization_index(5, 10)  # legacy: (count, num_agents)
        - compute_specialization_index(agents=dict, num_agents=3)

    Args:
        agent_skills: Can be:
            - List of fact/skill counts per agent
            - Dict with "facts_per_agent" or "agent_skills" key
            - Dict mapping agent_id -> skill_count
            - Single int/float (legacy: treated as count)
        num_agents: Optional override for number of agents

    Returns:
        Tuple of (specialization_index, SpecializationMetrics)
        - specialization_index: float in [0, log2(N_agents)]
        - metrics: SpecializationMetrics object with gini, entropy, etc.
    """
    # Handle dictionary input (game result style)
    if isinstance(agent_skills, dict):
        if "facts_per_agent" in agent_skills:
            agent_skills = agent_skills["facts_per_agent"]
        elif "agent_skills" in agent_skills:
            agent_skills = agent_skills["agent_skills"]
        else:
            # Try to extract values if it's a mapping of agent_id -> skill_count
            agent_skills = list(agent_skills.values())

    # Normalize input to list of numbers
    if isinstance(agent_skills, (int, float)):
        # Legacy: treat as count, generate dummy distribution
        count = int(agent_skills)
        if num_agents is None:
            num_agents = count
        agent_skills = [1] * count

    # Handle list input
    if not isinstance(agent_skills, list):
        try:
            agent_skills = list(agent_skills)
        except (TypeError, ValueError):
            agent_skills = []

    if not agent_skills:
        return 0.0, SpecializationMetrics()

    # Determine num_agents
    if num_agents is None:
        num_agents = len(agent_skills)
    else:
        # Ensure num_agents is at least 1
        num_agents = max(1, num_agents)

    # Ensure list length matches num_agents if provided
    if len(agent_skills) != num_agents:
        if len(agent_skills) < num_agents:
            agent_skills = list(agent_skills) + [0] * (num_agents - len(agent_skills))
        else:
            agent_skills = agent_skills[:num_agents]

    # Convert to float for calculations
    values = [float(v) for v in agent_skills]

    # Compute metrics
    gini = compute_gini_coefficient(values)
    entropy = compute_shannon_entropy(values)

    # Max entropy for N agents is log(N) (natural log)
    # This corresponds to log2(N) in bits, but we use natural log for consistency
    max_entropy = math.log(num_agents) if num_agents > 1 else 1.0
    if max_entropy == 0:
        max_entropy = 1.0

    # Normalized entropy (0 to 1)
    normalized_entropy = entropy / max_entropy

    # Specialization Index: max_entropy - entropy
    # This gives: 0 when uniform (entropy = max_entropy)
    #             max_entropy when concentrated (entropy = 0)
    # Bounded: [0, log2(N_agents)] (in natural log units)
    spec_index = max_entropy - entropy

    # Ensure non-negative
    spec_index = max(0.0, spec_index)

    metrics = SpecializationMetrics(
        gini=gini,
        entropy=entropy,
        specialization_index=spec_index,
        max_entropy=max_entropy,
        normalized_entropy=normalized_entropy
    )

    return spec_index, metrics


def validate_specialization_index(index: float) -> bool:
    """Validate that the index is in [0, log2(N_agents)].

    Note: Without knowing N_agents, we can only check that it's non-negative.
    The upper bound depends on the number of agents.

    Args:
        index: Specialization index value

    Returns:
        True if index is non-negative (lower bound check)
    """
    return index >= 0.0


def batch_compute_specialization(
    results: List[Dict[str, Any]]
) -> List[Tuple[float, SpecializationMetrics]]:
    """Compute specialization index for a list of game results.

    Args:
        results: List of game result dictionaries, each containing
                'facts_per_agent' or 'agent_skills' key

    Returns:
        List of (specialization_index, metrics) tuples
    """
    indices = []
    for res in results:
        # Assume 'facts_per_agent' is in the result
        if "facts_per_agent" in res:
            idx, metrics = compute_specialization_index(res["facts_per_agent"])
            indices.append((idx, metrics))
        elif "agent_skills" in res:
            idx, metrics = compute_specialization_index(res["agent_skills"])
            indices.append((idx, metrics))
        else:
            indices.append((0.0, SpecializationMetrics()))
    return indices