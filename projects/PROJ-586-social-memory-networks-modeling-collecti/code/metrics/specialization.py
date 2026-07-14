"""Specialization metrics for multi-agent social memory networks.

This module implements the computation of the specialization index, a
distribution-based metric measuring how facts/contributions are distributed
across agents in a collective memory system.

FR-004: Specialization Index
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
    gini_coefficient: Optional[float] = None
    shannon_entropy: Optional[float] = None
    per_agent_counts: List[int] = field(default_factory=list)
    total_facts: int = 0
    num_agents: int = 0


def compute_gini_coefficient(values: List[Union[int, float]]) -> float:
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
    cumsum = np.cumsum(sorted_values)

    # Gini formula: (2 * sum(i * x_i) - (n + 1) * sum(x_i)) / (n * sum(x_i))
    gini = (2.0 * np.sum((np.arange(1, n + 1) * sorted_values)) - (n + 1) * cumsum[-1]) / (n * cumsum[-1])
    return float(gini)


def compute_shannon_entropy(values: List[Union[int, float]]) -> float:
    """Compute Shannon entropy for a distribution.

    Args:
        values: List of non-negative values representing counts or probabilities.

    Returns:
        Shannon entropy in bits.
    """
    if not values or len(values) == 0:
        return 0.0

    values = np.array(values, dtype=float)
    total = np.sum(values)

    if total == 0:
        return 0.0

    # Normalize to probabilities
    probs = values / total

    # Filter out zero probabilities to avoid log(0)
    probs = probs[probs > 0]

    # Compute entropy: -sum(p * log2(p))
    entropy = -np.sum(probs * np.log2(probs))
    return float(entropy)


def compute_specialization_index(
    agent_fact_counts: Union[List[int], Dict[int, int], None],
    num_agents: Optional[int] = None
) -> Tuple[float, SpecializationMetrics]:
    """Compute the specialization index for a set of agents.

    The specialization index measures how unevenly facts are distributed among
    agents. It is bounded between 0 (perfect equality) and log2(N_agents)
    (perfect specialization where each agent knows disjoint facts).

    FR-004: Calculate distribution-based metric of per-agent fact contribution,
    bounded 0 to log2(N_agents).

    Args:
        agent_fact_counts: Either a list of fact counts per agent, or a dict
            mapping agent_id to fact count. If None or empty, returns 0.
        num_agents: Optional override for the number of agents. If not provided,
            inferred from the input.

    Returns:
        Tuple of (specialization_index, SpecializationMetrics).
        The index is bounded between 0 and log2(N_agents).

    Raises:
        ValueError: If inputs are invalid (negative counts, etc.).
    """
    # Handle None or empty input
    if agent_fact_counts is None:
        if num_agents is not None and num_agents > 0:
            counts = [0] * num_agents
            n_agents = num_agents
        else:
            return 0.0, SpecializationMetrics(
                specialization_index=0.0,
                per_agent_counts=[],
                total_facts=0,
                num_agents=0
            )
    elif isinstance(agent_fact_counts, dict):
        if not agent_fact_counts:
            counts = [0] * (num_agents or 0)
            n_agents = num_agents or 0
        else:
            # Extract counts, filling missing agents with 0
            max_id = max(agent_fact_counts.keys()) if agent_fact_counts else 0
            if num_agents is not None:
                n_agents = num_agents
            else:
                n_agents = max_id + 1
            counts = [agent_fact_counts.get(i, 0) for i in range(n_agents)]
    else:
        # Assume it's a list
        if not agent_fact_counts:
            counts = []
            n_agents = 0
        else:
            counts = list(agent_fact_counts)
            n_agents = len(counts)
            if num_agents is not None:
                n_agents = num_agents
                # Pad or truncate if needed
                if len(counts) < n_agents:
                    counts.extend([0] * (n_agents - len(counts)))
                elif len(counts) > n_agents:
                    counts = counts[:n_agents]

    # Validate counts
    for i, c in enumerate(counts):
        if c < 0:
            raise ValueError(f"Negative fact count for agent {i}: {c}")

    total_facts = sum(counts)

    # If no facts or no agents, specialization is 0
    if total_facts == 0 or n_agents <= 1:
        return 0.0, SpecializationMetrics(
            specialization_index=0.0,
            per_agent_counts=counts,
            total_facts=total_facts,
            num_agents=n_agents,
            gini_coefficient=0.0,
            shannon_entropy=0.0
        )

    # Compute Shannon entropy of the distribution
    entropy = compute_shannon_entropy(counts)

    # Maximum possible entropy (uniform distribution) is log2(N_agents)
    max_entropy = math.log2(n_agents) if n_agents > 1 else 1.0

    # Specialization index: normalized by max entropy, scaled to [0, log2(N)]
    # High entropy = diverse knowledge (low specialization)
    # Low entropy = concentrated knowledge (high specialization)
    # We invert: specialization = max_entropy - entropy
    # Then bound to [0, max_entropy]
    raw_specialization = max_entropy - entropy
    specialization_index = max(0.0, min(max_entropy, raw_specialization))

    # Also compute Gini coefficient as a secondary metric
    gini = compute_gini_coefficient(counts)

    metrics = SpecializationMetrics(
        specialization_index=specialization_index,
        per_agent_counts=counts,
        total_facts=total_facts,
        num_agents=n_agents,
        gini_coefficient=gini,
        shannon_entropy=entropy
    )

    return specialization_index, metrics


def validate_specialization_index(
    index: float,
    num_agents: int,
    tolerance: float = 1e-6
) -> bool:
    """Validate that a specialization index is within expected bounds.

    Args:
        index: The computed specialization index.
        num_agents: Number of agents in the system.
        tolerance: Floating point tolerance for boundary checks.

    Returns:
        True if the index is within [0, log2(N_agents)], False otherwise.
    """
    if num_agents <= 0:
        return index == 0.0

    max_val = math.log2(num_agents)
    return -tolerance <= index <= (max_val + tolerance)


def batch_compute_specialization(
    game_results: List[Dict[str, Any]]
) -> List[Tuple[float, SpecializationMetrics]]:
    """Compute specialization index for multiple games.

    Args:
        game_results: List of game result dictionaries, each containing
            'agent_fact_counts' or similar structure.

    Returns:
        List of (specialization_index, metrics) tuples.
    """
    results = []
    for game in game_results:
        counts = game.get('agent_fact_counts', game.get('facts_per_agent', []))
        num_agents = game.get('num_agents', None)
        idx, metrics = compute_specialization_index(counts, num_agents=num_agents)
        results.append((idx, metrics))
    return results