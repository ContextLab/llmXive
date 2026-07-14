"""Specialization metrics for multi-agent social memory networks.

Calculates distribution-based metrics of per-agent fact contribution.
The specialization index is bounded between 0 and log2(N_agents).
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
    specialization_index: float
    gini_coefficient: float
    shannon_entropy: float
    max_specialization_index: float
    agent_contributions: Dict[int, int] = field(default_factory=dict)


def compute_gini_coefficient(values: List[float]) -> float:
    """Compute the Gini coefficient for a list of values.

    The Gini coefficient measures inequality in a distribution.
    0 = perfect equality, 1 = perfect inequality.

    Args:
        values: List of non-negative numeric values.

    Returns:
        Gini coefficient between 0 and 1.
    """
    if not values or len(values) == 0:
        return 0.0

    values = np.array(values, dtype=float)
    if np.all(values == 0):
        return 0.0

    n = len(values)
    sorted_values = np.sort(values)
    cumulative = np.cumsum(sorted_values)

    gini = (2 * np.sum((np.arange(1, n + 1) * sorted_values))) / (n * np.sum(values)) - (n + 1) / n
    return max(0.0, min(1.0, gini))


def compute_shannon_entropy(values: List[float]) -> float:
    """Compute Shannon entropy for a distribution.

    Args:
        values: List of non-negative numeric values representing counts or weights.

    Returns:
        Shannon entropy in bits. Returns 0 if all values are zero.
    """
    if not values or len(values) == 0:
        return 0.0

    if total == 0:
        return 0.0

    # Normalize to probabilities
    probs = [v / total for v in values if v > 0]

    if not probs:
        return 0.0

    # Compute entropy: -sum(p * log2(p))
    entropy = -sum(p * math.log2(p) for p in probs if p > 0)
    return entropy


def compute_specialization_index(
    facts: Union[List[Any], Dict[int, List[Any]], None],
    num_agents: Optional[int] = None,
    agents: Optional[Union[List[Any], Dict[int, Any]]] = None
) -> Tuple[float, SpecializationMetrics]:
    """Compute the specialization index for a multi-agent system.

    The specialization index measures how unevenly facts are distributed
    across agents. It is bounded between 0 (perfectly uniform distribution)
    and log2(N_agents) (perfect specialization where each agent knows
    disjoint sets of facts).

    Args:
        facts: Can be:
            - A list of facts where each fact is associated with an agent
              (e.g., list of agent IDs or tuples of (agent_id, fact))
            - A dictionary mapping agent_id to list of facts they know
            - None or empty list for edge cases
        num_agents: Total number of agents in the system. If None, inferred
            from the data.
        agents: Alternative representation of agent data (for compatibility
            with various call signatures).

    Returns:
        Tuple of (specialization_index, SpecializationMetrics)
        - specialization_index: float in [0, log2(N_agents)]
        - SpecializationMetrics: detailed metrics including Gini and entropy

    Raises:
        ValueError: If inputs are inconsistent or invalid.
    """
    # Handle edge cases
    if facts is None:
        return 0.0, SpecializationMetrics(
            specialization_index=0.0,
            gini_coefficient=0.0,
            shannon_entropy=0.0,
            max_specialization_index=0.0,
            agent_contributions={}
        )

    # Parse facts into per-agent counts
    agent_fact_counts: Dict[int, int] = {}

    if isinstance(facts, dict):
        # facts is {agent_id: [list of facts]}
        agent_fact_counts = {k: len(v) if v else 0 for k, v in facts.items()}
    elif isinstance(facts, list):
        if len(facts) == 0:
            return 0.0, SpecializationMetrics(
                specialization_index=0.0,
                gini_coefficient=0.0,
                shannon_entropy=0.0,
                max_specialization_index=0.0,
                agent_contributions={}
            )

        # Check if facts are agent IDs or (agent_id, fact) tuples
        if len(facts) > 0 and isinstance(facts[0], tuple) and len(facts[0]) >= 1:
            # List of (agent_id, fact) or similar tuples
            agent_fact_counts = Counter(f[0] for f in facts if f)
        else:
            # List of agent IDs
            agent_fact_counts = Counter(facts)
    else:
        # Try to handle other iterable types
        try:
            agent_fact_counts = Counter(facts)
        except (TypeError, ValueError):
            return 0.0, SpecializationMetrics(
                specialization_index=0.0,
                gini_coefficient=0.0,
                shannon_entropy=0.0,
                max_specialization_index=0.0,
                agent_contributions={}
            )

    # Determine number of agents
    if num_agents is None:
        if agents is not None:
            if isinstance(agents, dict):
                num_agents = len(agents)
            elif isinstance(agents, list):
                num_agents = len(agents)
            else:
                num_agents = max(agent_fact_counts.keys(), default=0) + 1
        else:
            num_agents = max(agent_fact_counts.keys(), default=0) + 1
            # Ensure we count all agents from 0 to num_agents-1
            for i in range(num_agents):
                if i not in agent_fact_counts:
                    agent_fact_counts[i] = 0

    if num_agents <= 0:
        return 0.0, SpecializationMetrics(
            specialization_index=0.0,
            gini_coefficient=0.0,
            shannon_entropy=0.0,
            max_specialization_index=0.0,
            agent_contributions=dict(agent_fact_counts)
        )

    # Ensure all agents are represented
    for i in range(num_agents):
        if i not in agent_fact_counts:
            agent_fact_counts[i] = 0

    # Extract counts as a list
    counts = [agent_fact_counts.get(i, 0) for i in range(num_agents)]

    # Compute max possible specialization index: log2(N_agents)
    max_specialization_index = math.log2(num_agents) if num_agents > 1 else 0.0

    # If all counts are zero, specialization is 0
    total_facts = sum(counts)
    if total_facts == 0:
        return 0.0, SpecializationMetrics(
            specialization_index=0.0,
            gini_coefficient=0.0,
            shannon_entropy=0.0,
            max_specialization_index=max_specialization_index,
            agent_contributions=dict(agent_fact_counts)
        )

    # Compute Shannon entropy of the distribution
    shannon_entropy = compute_shannon_entropy(counts)

    # Compute Gini coefficient
    gini_coefficient = compute_gini_coefficient(counts)

    # The specialization index is based on the deviation from uniform distribution.
    # A uniform distribution has entropy log2(N_agents).
    # Specialization = max_entropy - actual_entropy = log2(N) - H
    # This ranges from 0 (uniform) to log2(N) (perfect specialization)
    max_entropy = math.log2(num_agents) if num_agents > 1 else 0.0
    specialization_index = max_entropy - shannon_entropy

    # Ensure bounds
    specialization_index = max(0.0, min(max_specialization_index, specialization_index))

    return specialization_index, SpecializationMetrics(
        specialization_index=specialization_index,
        gini_coefficient=gini_coefficient,
        shannon_entropy=shannon_entropy,
        max_specialization_index=max_specialization_index,
        agent_contributions=dict(agent_fact_counts)
    )


def validate_specialization_index(
    index: float,
    num_agents: int,
    tolerance: float = 1e-6
) -> Tuple[bool, str]:
    """Validate that a specialization index is within expected bounds.

    Args:
        index: The computed specialization index.
        num_agents: Number of agents in the system.
        tolerance: Allowed numerical tolerance for boundary checks.

    Returns:
        Tuple of (is_valid, error_message). If valid, error_message is empty.
    """
    if num_agents <= 0:
        return False, "num_agents must be positive"

    max_index = math.log2(num_agents) if num_agents > 1 else 0.0

    if index < -tolerance:
        return False, f"Specialization index {index} is negative"

    if index > max_index + tolerance:
        return False, f"Specialization index {index} exceeds maximum {max_index} for {num_agents} agents"

    return True, ""


def batch_compute_specialization(
    game_results: List[Dict[str, Any]]
) -> List[Tuple[float, SpecializationMetrics]]:
    """Compute specialization index for multiple games.

    Args:
        game_results: List of game result dictionaries, each containing
            'agent_facts' or similar structure.

    Returns:
        List of (specialization_index, metrics) tuples for each game.
    """
    results = []
    for game in game_results:
        agent_facts = game.get('agent_facts', game.get('facts', {}))
        num_agents = game.get('num_agents', game.get('agents', 0))

        idx, metrics = compute_specialization_index(
            facts=agent_facts,
            num_agents=num_agents
        )
        results.append((idx, metrics))

    return results


def compute_specialization_index_v1(
    agent_skills: Union[List[int], Dict[int, int], List[Dict]],
    num_agents: Optional[int] = None
) -> Tuple[float, SpecializationMetrics]:
    """Legacy wrapper for backward compatibility.

    Args:
        agent_skills: Can be a list of skill counts per agent, or a dict
            mapping agent_id to skill count.
        num_agents: Total number of agents (optional, inferred if not provided).

    Returns:
        Tuple of (specialization_index, metrics).
    """
    if isinstance(agent_skills, list):
        # Convert list to dict: {i: count}
        if num_agents is None:
            num_agents = len(agent_skills)
        facts_dict = {i: agent_skills[i] for i in range(len(agent_skills))}
        return compute_specialization_index(facts_dict, num_agents=num_agents)
    elif isinstance(agent_skills, dict):
        return compute_specialization_index(agent_skills, num_agents=num_agents)
    else:
        return compute_specialization_index(agent_skills, num_agents=num_agents)