"""Specialization metrics for multi-agent memory networks.

This module implements the computation of the specialization index, a
distribution-based metric measuring how facts/contributions are distributed
across agents in a collective memory system.

The specialization index is bounded between 0 and log2(N_agents), where:
- 0 indicates perfect equal contribution (no specialization)
- log2(N_agents) indicates perfect specialization (one agent holds all facts)
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

@dataclass
class SpecializationMetrics:
    """Container for specialization computation results.

    Attributes:
        specialization_index: The computed specialization index (0 to log2(N))
        gini_coefficient: Gini coefficient of contribution distribution (0 to 1)
        shannon_entropy: Shannon entropy of contribution distribution
        max_entropy: Maximum possible entropy (log2(N))
        normalized_index: Specialization index normalized to [0, 1]
        agent_contributions: Dict mapping agent_id to contribution count
    """
    specialization_index: float
    gini_coefficient: float
    shannon_entropy: float
    max_entropy: float
    normalized_index: float
    agent_contributions: Dict[int, int] = field(default_factory=dict)


def compute_gini_coefficient(values: List[float]) -> float:
    """Compute the Gini coefficient for a list of values.

def compute_gini_coefficient(values: List[float]) -> float:
    """
    Compute the Gini coefficient for a list of values.
    
    The Gini coefficient measures inequality in a distribution.
    0 = perfect equality, 1 = perfect inequality.
    
    Args:
        values: List of non-negative numeric values

    Returns:
        Gini coefficient in range [0, 1]
    """
    if not values or len(values) == 0:
        return 0.0

    values = np.array(values, dtype=float)
    if np.sum(values) == 0:
        return 0.0

    n = len(values)
    sorted_values = np.sort(values)
    cumsum = np.cumsum(sorted_values)

    # Gini formula: (2 * sum(i * x_i) - (n+1) * sum(x_i)) / (n * sum(x_i))
    gini = (2 * np.sum((np.arange(1, n + 1) * sorted_values)) - (n + 1) * np.sum(values)) / (n * np.sum(values))

    return float(max(0.0, min(1.0, gini)))


def compute_shannon_entropy(values: List[float], base: float = 2.0) -> float:
    """Compute Shannon entropy of a distribution.

    Args:
        values: List of non-negative values (will be normalized to probabilities)
        base: Logarithm base (default 2 for bits)

    Returns:
        Shannon entropy in bits (or specified base units)
    """
    if not values or len(values) == 0:
        return 0.0

    values = np.array(values, dtype=float)
    total = np.sum(values)

    if total == 0:
        return 0.0

    probabilities = values / total
    # Filter out zero probabilities to avoid log(0)
    probabilities = probabilities[probabilities > 0]

    entropy = -np.sum(probabilities * np.log(probabilities) / np.log(base))
    return float(entropy)

def compute_specialization_index(
    facts_per_agent: Union[List[int], Dict[int, int], List[Dict[str, Any]], None],
    num_agents: Optional[int] = None,
    agent_id_key: str = "agent_id",
    fact_count_key: str = "fact_count",
) -> Tuple[float, SpecializationMetrics]:
    """Compute the specialization index for a multi-agent system.

    The specialization index measures how unevenly facts/contributions are
    distributed across agents. It is based on the ratio of observed entropy
    to maximum possible entropy.

    Formula:
        specialization_index = log2(N) - H(P)
        normalized = 1 - (H(P) / log2(N))

    Where:
        N = number of agents
        H(P) = Shannon entropy of the contribution distribution
        P = normalized contribution proportions

    The index ranges from 0 (perfect equality) to log2(N) (perfect specialization).

    Args:
        facts_per_agent: Can be one of:
            - List[int]: Direct list of fact counts per agent
            - Dict[int, int]: Mapping of agent_id -> fact_count
            - List[Dict]: List of agent records with count fields
            - None or empty: Returns 0 with default metrics
        num_agents: Total number of agents (optional, inferred from data if not provided)
        agent_id_key: Key for agent ID in dict/list records
        fact_count_key: Key for fact count in dict/list records

    Returns:
        Tuple of (specialization_index, SpecializationMetrics)
    """
    # Handle empty/None input
    if facts_per_agent is None:
        return 0.0, SpecializationMetrics(
            specialization_index=0.0,
            gini_coefficient=0.0,
            shannon_entropy=0.0,
            max_entropy=0.0,
            normalized_index=0.0,
            agent_contributions={},
        )

    # Convert various input formats to a list of counts
    counts: List[int] = []
    agent_ids: List[int] = []
    agent_contributions: Dict[int, int] = {}

    if isinstance(facts_per_agent, dict):
        # Dict[int, int] format
        agent_ids = list(facts_per_agent.keys())
        counts = list(facts_per_agent.values())
        agent_contributions = dict(facts_per_agent)
    elif isinstance(facts_per_agent, list):
        if len(facts_per_agent) == 0:
            return 0.0, SpecializationMetrics(
                specialization_index=0.0,
                gini_coefficient=0.0,
                shannon_entropy=0.0,
                max_entropy=0.0,
                normalized_index=0.0,
                agent_contributions={},
            )

        if isinstance(facts_per_agent[0], dict):
            # List of dicts format
            for record in facts_per_agent:
                aid = record.get(agent_id_key, 0)
                fcount = record.get(fact_count_key, 0)
                agent_ids.append(aid)
                counts.append(int(fcount))
                agent_contributions[int(aid)] = int(fcount)
        elif isinstance(facts_per_agent[0], (int, float)):
            # Direct list of counts
            counts = [int(x) for x in facts_per_agent]
            agent_ids = list(range(len(counts)))
            agent_contributions = {i: counts[i] for i in range(len(counts))}
        else:
            return 0.0, SpecializationMetrics(
                specialization_index=0.0,
                gini_coefficient=0.0,
                shannon_entropy=0.0,
                max_entropy=0.0,
                normalized_index=0.0,
                agent_contributions={},
            )
    else:
        return 0.0, SpecializationMetrics(
            specialization_index=0.0,
            gini_coefficient=0.0,
            shannon_entropy=0.0,
            max_entropy=0.0,
            normalized_index=0.0,
            agent_contributions={},
        )

    # Determine number of agents
    if num_agents is None:
        num_agents = len(agent_ids) if agent_ids else len(counts)

    if num_agents <= 0:
        num_agents = max(1, len(counts))

    # Ensure counts list has exactly num_agents entries
    # Pad with zeros if needed, or truncate if too long
    while len(counts) < num_agents:
        counts.append(0)
    if len(counts) > num_agents:
        counts = counts[:num_agents]

    # Compute total facts
    total_facts = sum(counts)

    if total_facts == 0:
        # No facts distributed - perfect equality by default
        return 0.0, SpecializationMetrics(
            specialization_index=0.0,
            gini_coefficient=0.0,
            shannon_entropy=0.0,
            max_entropy=math.log2(num_agents) if num_agents > 1 else 0.0,
            normalized_index=0.0,
            agent_contributions=agent_contributions,
        )

    # Compute entropy-based metrics
    max_entropy = math.log2(num_agents) if num_agents > 1 else 0.0
    shannon_entropy = compute_shannon_entropy(counts, base=2.0)

    # Specialization index: log2(N) - H(P)
    # This measures deviation from uniform distribution
    specialization_index = max_entropy - shannon_entropy

    # Ensure bounds [0, log2(N)]
    specialization_index = max(0.0, min(max_entropy, specialization_index))

    # Normalized index [0, 1]
    normalized_index = specialization_index / max_entropy if max_entropy > 0 else 0.0

    # Gini coefficient
    gini = compute_gini_coefficient(counts)

    metrics = SpecializationMetrics(
        specialization_index=specialization_index,
        gini_coefficient=gini,
        shannon_entropy=shannon_entropy,
        max_entropy=max_entropy,
        normalized_index=normalized_index,
        agent_contributions=agent_contributions,
    )

def validate_specialization_index(
    index: float,
    num_agents: int,
    tolerance: float = 1e-6,
) -> Tuple[bool, str]:
    """Validate that a specialization index is within expected bounds.

    Args:
        index: Computed specialization index value
        num_agents: Number of agents in the system
        tolerance: Floating point tolerance for bounds checking

    Returns:
        Tuple of (is_valid, error_message)
    """
    if num_agents <= 0:
        return False, "num_agents must be positive"

    max_index = math.log2(num_agents) if num_agents > 1 else 0.0

    if index < -tolerance:
        return False, f"Specialization index {index} is below lower bound 0"

    if index > max_index + tolerance:
        return False, f"Specialization index {index} exceeds upper bound {max_index}"

    return True, "OK"


def batch_compute_specialization(
    game_results: List[Dict[str, Any]],
    agent_count_key: str = "agent_count",
    facts_key: str = "facts_per_agent",
) -> List[Tuple[float, SpecializationMetrics]]:
    """Compute specialization index for multiple game results.

    Args:
        game_results: List of game result dictionaries
        agent_count_key: Key for agent count in result dict
        facts_key: Key for facts_per_agent in result dict

    Returns:
        List of (specialization_index, metrics) tuples for each game
    """
    results = []
    for result in game_results:
        agent_count = result.get(agent_count_key, 0)
        facts = result.get(facts_key, None)

        if facts is not None:
            idx, metrics = compute_specialization_index(facts, num_agents=agent_count)
            results.append((idx, metrics))
        else:
            # Skip games without facts data
            results.append((0.0, SpecializationMetrics(
                specialization_index=0.0,
                gini_coefficient=0.0,
                shannon_entropy=0.0,
                max_entropy=0.0,
                normalized_index=0.0,
                agent_contributions={},
            )))

    return results