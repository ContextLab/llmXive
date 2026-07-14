"""Specialization metrics for multi-agent memory networks.

Computes distribution-based metrics of per-agent fact contribution,
bounded between 0 and log2(N_agents).
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
    gini_coefficient: float
    shannon_entropy: float
    specialization_index: float
    max_specialization: float
    agent_contributions: Dict[int, int] = field(default_factory=dict)


def compute_gini_coefficient(values: List[float]) -> float:
    """Compute Gini coefficient for a list of values.

    Args:
        values: List of non-negative numeric values.

    Returns:
        Gini coefficient in range [0, 1].
    """
    if not values or len(values) == 0:
        return 0.0

    values = np.array(values, dtype=float)
    if np.sum(values) == 0:
        return 0.0

    n = len(values)
    values_sorted = np.sort(values)
    cumsum = np.cumsum(values_sorted)
    gini = (2.0 * np.sum((np.arange(1, n + 1) * values_sorted))) / (n * np.sum(values)) - (n + 1) / n
    return max(0.0, min(1.0, gini))


def compute_shannon_entropy(values: List[float], base: float = 2.0) -> float:
    """Compute Shannon entropy for a list of values.

    Args:
        values: List of non-negative numeric values.
        base: Logarithm base (default 2 for bits).

    Returns:
        Shannon entropy in units of log_base.
    """
    if not values or len(values) == 0:
        return 0.0

    values = np.array(values, dtype=float)
    total = np.sum(values)
    if total == 0:
        return 0.0

    probabilities = values / total
    # Filter out zeros to avoid log(0)
    probabilities = probabilities[probabilities > 0]
    entropy = -np.sum(probabilities * np.log(probabilities) / np.log(base))
    return float(entropy)


def compute_specialization_index(
    agent_facts: Union[Dict[int, List[Any]], List[List[Any]], None],
    num_agents: Optional[int] = None,
    agents: Optional[Union[Dict[int, List[Any]], List[List[Any]]]] = None
) -> Tuple[float, SpecializationMetrics]:
    """Compute specialization index based on distribution of fact contributions.

    The specialization index measures how unevenly facts are distributed
    among agents. A value of 0 indicates perfect equal distribution (no
    specialization), while the maximum value is log2(N_agents), indicating
    perfect specialization (each agent owns unique facts).

    Args:
        agent_facts: Dictionary mapping agent_id -> list of facts, OR
                    list of lists where index is agent_id.
                    Can also be None or empty for edge cases.
        num_agents: Explicit number of agents (optional, inferred if not provided).
        agents: Alternative parameter name for agent_facts (for API compatibility).

    Returns:
        Tuple of (specialization_index, SpecializationMetrics).
        specialization_index is bounded [0, log2(N_agents)].
    """
    # Handle alternative parameter names and edge cases
    if agents is not None and agent_facts is None:
        agent_facts = agents
    if agent_facts is None:
        agent_facts = {}

    # Normalize to dict format
    if isinstance(agent_facts, list):
        agent_facts = {i: facts for i, facts in enumerate(agent_facts)}

    if not agent_facts:
        # No data - return zero specialization
        return 0.0, SpecializationMetrics(
            gini_coefficient=0.0,
            shannon_entropy=0.0,
            specialization_index=0.0,
            max_specialization=0.0,
            agent_contributions={}
        )

    # Infer num_agents if not provided
    if num_agents is None:
        num_agents = len(agent_facts)

    if num_agents <= 0:
        return 0.0, SpecializationMetrics(
            gini_coefficient=0.0,
            shannon_entropy=0.0,
            specialization_index=0.0,
            max_specialization=0.0,
            agent_contributions={}
        )

    # Count facts per agent
    contributions = {agent_id: len(facts) for agent_id, facts in agent_facts.items()}
    values = list(contributions.values())

    # Pad with zeros if some agents have no facts
    while len(values) < num_agents:
        values.append(0)
    values = values[:num_agents]

    # Compute metrics
    gini = compute_gini_coefficient(values)
    entropy = compute_shannon_entropy(values)
    max_entropy = math.log2(num_agents) if num_agents > 1 else 1.0

    # Specialization index: normalized entropy deficit
    # 0 = uniform distribution (no specialization)
    # max = log2(N) = perfect specialization
    if max_entropy > 0:
        # Higher entropy = more uniform = lower specialization
        # We want: specialization = max_entropy - entropy
        specialization_index = max(0.0, max_entropy - entropy)
    else:
        specialization_index = 0.0

    # Ensure bounds [0, log2(N_agents)]
    max_specialization = math.log2(num_agents) if num_agents > 1 else 0.0
    specialization_index = max(0.0, min(specialization_index, max_specialization))

    metrics = SpecializationMetrics(
        gini_coefficient=gini,
        shannon_entropy=entropy,
        specialization_index=specialization_index,
        max_specialization=max_specialization,
        agent_contributions=contributions
    )

    return specialization_index, metrics


def validate_specialization_index(index: float, num_agents: int) -> bool:
    """Validate that specialization index is within expected bounds.

    Args:
        index: Computed specialization index value.
        num_agents: Number of agents in the system.

    Returns:
        True if index is in valid range [0, log2(N_agents)].
    """
    if num_agents <= 0:
        return index == 0.0

    max_val = math.log2(num_agents)
    return 0.0 <= index <= max_val


def batch_compute_specialization(
    games: List[Dict[str, Any]],
    agent_facts_key: str = "agent_facts",
    num_agents_key: str = "num_agents"
) -> List[Tuple[float, SpecializationMetrics]]:
    """Compute specialization index for multiple games.

    Args:
        games: List of game result dictionaries.
        agent_facts_key: Key for agent facts in game dict.
        num_agents_key: Key for number of agents in game dict.

    Returns:
        List of (specialization_index, metrics) tuples for each game.
    """
    results = []
    for game in games:
        agent_facts = game.get(agent_facts_key, {})
        num_agents = game.get(num_agents_key, len(agent_facts) if isinstance(agent_facts, dict) else 0)
        idx, metrics = compute_specialization_index(agent_facts, num_agents)
        results.append((idx, metrics))
    return results


def compute_specialization_index_v1(
    agent_skills: Union[Dict[int, List[Any]], List[List[Any]]],
    num_agents: Optional[int] = None
) -> Tuple[float, SpecializationMetrics]:
    """Legacy alias for compute_specialization_index (v1 compatibility)."""
    return compute_specialization_index(agent_skills, num_agents)

# Internal helper for self-test / recursive usage
def _compute_from_dict(facts_dict: Dict[int, List[Any]], num_agents: int) -> Tuple[float, SpecializationMetrics]:
    """Internal helper matching legacy call patterns."""
    return compute_specialization_index(facts_dict, num_agents)

def _compute_from_list(agent_skills: List[List[Any]], num_agents: int) -> Tuple[float, SpecializationMetrics]:
    """Internal helper matching legacy call patterns."""
    return compute_specialization_index(agent_skills, num_agents)