"""Specialization metrics for multi-agent social memory networks.

This module implements the computation of specialization indices based on
the Gini coefficient and Shannon entropy, as referenced in the project's
research design (FR-004).

The specialization index measures how unevenly knowledge/skills are distributed
among agents in a group. High specialization implies that different agents
hold distinct pieces of information (transactive memory system), while low
specialization implies redundancy.

References:
- Gini coefficient: https://en.wikipedia.org/wiki/Gini_coefficient
- Shannon entropy: https://en.wikipedia.org/wiki/Entropy_(information_theory)
- Transactive Memory Systems: Wegner et al. (1985)
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, List, Tuple, Optional, Union

import numpy as np


@dataclass
class SpecializationMetrics:
    """Container for specialization-related metrics."""
    gini_coefficient: float = 0.0
    shannon_entropy: float = 0.0
    normalized_entropy: float = 0.0
    specialization_index: float = 0.0
    agent_skill_counts: List[int] = field(default_factory=list)
    total_skills: int = 0
    num_agents: int = 0


def compute_gini_coefficient(values: List[Union[int, float]]) -> float:
    """Compute the Gini coefficient for a list of values.

    The Gini coefficient measures inequality among values in a distribution.
    In the context of transactive memory, it measures inequality in knowledge
    distribution across agents.

    Args:
        values: List of non-negative values (e.g., number of facts known per agent).

    Returns:
        Gini coefficient between 0 (perfect equality) and 1 (perfect inequality).
    """
    if not values or len(values) == 0:
        return 0.0

    values = [float(v) for v in values]
    n = len(values)
    total = sum(values)

    if total == 0:
        return 0.0

    # Sort the values
    sorted_values = sorted(values)

    # Compute the Gini coefficient using the formula:
    # G = (2 * sum(i * x_i) - (n + 1) * sum(x_i)) / (n * sum(x_i))
    # where i is the rank (1-indexed)
    cumsum = 0.0
    weighted_sum = 0.0
    for i, val in enumerate(sorted_values, start=1):
        weighted_sum += i * val
        cumsum += val

    if cumsum == 0:
        return 0.0

    gini = (2.0 * weighted_sum - (n + 1) * cumsum) / (n * cumsum)
    return max(0.0, min(1.0, gini))


def compute_shannon_entropy(values: List[Union[int, float]]) -> float:
    """Compute Shannon entropy for a distribution of values.

    Shannon entropy measures the uncertainty or diversity in a distribution.
    For specialization, we normalize it to measure how "spread out" the
    knowledge is across agents.

    Args:
        values: List of non-negative values representing counts or weights.

    Returns:
        Shannon entropy value (higher means more uniform distribution).
    """
    if not values or len(values) == 0:
        return 0.0

    values = [float(v) for v in values]
    total = sum(values)

    if total == 0:
        return 0.0

    # Convert to probabilities
    probs = [v / total for v in values if v > 0]

    if not probs:
        return 0.0

    # Compute entropy: -sum(p * log(p))
    entropy = 0.0
    for p in probs:
        if p > 0:
            entropy -= p * math.log(p)

    return entropy


def compute_specialization_index(
    agent_list: Optional[Union[List[Any], List[int], List[float]]] = None,
    num_agents: Optional[int] = None,
    agents: Optional[Union[List[Any], List[int], List[float]]] = None,
    game_id: Optional[int] = None,
) -> Tuple[float, SpecializationMetrics]:
    """Compute the specialization index for a group of agents.

    This function calculates the specialization index based on the distribution
    of skills/knowledge among agents. The index is derived from the Gini
    coefficient, which measures inequality in the distribution.

    The function supports multiple calling patterns for backward compatibility:
    1. compute_specialization_index(agent_list) - list of agent skills
    2. compute_specialization_index(agent_list, num_agents=N) - with explicit count
    3. compute_specialization_index(agents=..., num_agents=...) - keyword style
    4. compute_specialization_index(agent_count, game_id) - legacy (uses agent_count as list length)
    5. compute_specialization_index([]) - empty list

    Args:
        agent_list: List of agent skill counts or agent objects. If agents are
            objects, they should have a 'skill_count' or similar attribute.
        num_agents: Optional explicit number of agents. If None, inferred from list.
        agents: Alternative keyword argument for agent list.
        game_id: Optional game identifier (ignored in computation, kept for legacy).

    Returns:
        A tuple of (specialization_index, metrics_dataclass).
        - specialization_index: A value between 0 and 1, where higher means
          more specialized (unequal) distribution.
        - metrics_dataclass: Full metrics including Gini coefficient, entropy, etc.
    """
    # Handle alternative argument names
    if agent_list is None and agents is not None:
        agent_list = agents

    # Handle legacy call: (agent_count, game_id) where agent_count is actually a list length
    if agent_list is not None and num_agents is None and game_id is not None:
        # If agent_list looks like a single integer, treat it as a count
        if isinstance(agent_list, int):
            # Create a dummy list of zeros with that length
            agent_list = [0] * agent_list

    # Handle empty or None input
    if agent_list is None or len(agent_list) == 0:
        if num_agents and num_agents > 0:
            skill_counts = [0] * num_agents
        else:
            skill_counts = []
    else:
        # Extract skill counts if agents are objects
        skill_counts = []
        for item in agent_list:
            if isinstance(item, (int, float)):
                skill_counts.append(int(item))
            elif hasattr(item, 'skill_count'):
                skill_counts.append(int(item.skill_count))
            elif hasattr(item, 'knowledge_count'):
                skill_counts.append(int(item.knowledge_count))
            else:
                # Assume it's already a count
                skill_counts.append(1)

    num_agents_actual = num_agents if num_agents is not None else len(skill_counts)

    # If we have counts but num_agents was specified and differs, pad or truncate
    if num_agents_actual != len(skill_counts):
        if len(skill_counts) < num_agents_actual:
            skill_counts.extend([0] * (num_agents_actual - len(skill_counts)))
        elif len(skill_counts) > num_agents_actual:
            skill_counts = skill_counts[:num_agents_actual]

    # Compute metrics
    gini = compute_gini_coefficient(skill_counts)
    entropy = compute_shannon_entropy(skill_counts)

    # Normalized entropy (0 to 1, where 1 is maximum diversity)
    if num_agents_actual > 1:
        max_entropy = math.log(num_agents_actual)
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0.0
    else:
        normalized_entropy = 0.0 if entropy == 0 else 1.0

    # Specialization index: higher Gini = more specialization
    # We use Gini directly as the specialization index
    specialization_index = gini

    metrics = SpecializationMetrics(
        gini_coefficient=gini,
        shannon_entropy=entropy,
        normalized_entropy=normalized_entropy,
        specialization_index=specialization_index,
        agent_skill_counts=skill_counts,
        total_skills=sum(skill_counts),
        num_agents=num_agents_actual,
    )

    return specialization_index, metrics


def validate_specialization_index(index: float) -> bool:
    """Validate that a specialization index is within expected bounds.

    Args:
        index: The specialization index value to validate.

    Returns:
        True if the index is in [0, 1], False otherwise.
    """
    return 0.0 <= index <= 1.0


def validate_specialization_metrics(metrics: SpecializationMetrics) -> bool:
    """Validate a SpecializationMetrics object.

    Args:
        metrics: The metrics object to validate.

    Returns:
        True if all fields are within expected ranges.
    """
    if not validate_specialization_index(metrics.specialization_index):
        return False
    if not validate_specialization_index(metrics.gini_coefficient):
        return False
    if metrics.shannon_entropy < 0:
        return False
    if metrics.normalized_entropy < 0 or metrics.normalized_entropy > 1:
        return False
    if metrics.num_agents < 0:
        return False
    if metrics.total_skills < 0:
        return False
    return True


def batch_compute_specialization(
    game_results: List[Any],
    agent_count: int,
) -> List[Tuple[float, SpecializationMetrics]]:
    """Compute specialization indices for multiple games.

    Args:
        game_results: List of game result objects. Each should expose agent
            skill counts via an attribute or method.
        agent_count: Expected number of agents per game.

    Returns:
        List of (specialization_index, metrics) tuples for each game.
    """
    results = []
    for game in game_results:
        # Extract skill counts from game result
        # Assume game has a 'agent_skills' attribute which is a list of counts
        if hasattr(game, 'agent_skills'):
            skills = game.agent_skills
        elif hasattr(game, 'skills'):
            skills = game.skills
        else:
            # Fallback: assume uniform distribution if we can't extract
            skills = [0] * agent_count

        idx, metrics = compute_specialization_index(
            agent_list=skills,
            num_agents=agent_count,
        )
        results.append((idx, metrics))
    return results


def compute_game_level_specialization(
    agent_skills: List[int],
    num_agents: int,
) -> Tuple[float, Dict[str, Any]]:
    """Compute specialization metrics at the game level.

    This is a convenience wrapper that returns a dictionary of metrics
    suitable for serialization or logging.

    Args:
        agent_skills: List of skill counts per agent.
        num_agents: Number of agents (should match len(agent_skills)).

    Returns:
        Tuple of (specialization_index, metrics_dict).
    """
    idx, metrics = compute_specialization_index(
        agent_list=agent_skills,
        num_agents=num_agents,
    )
    return idx, {
        'specialization_index': metrics.specialization_index,
        'gini_coefficient': metrics.gini_coefficient,
        'shannon_entropy': metrics.shannon_entropy,
        'normalized_entropy': metrics.normalized_entropy,
        'total_skills': metrics.total_skills,
        'num_agents': metrics.num_agents,
        'agent_skill_counts': metrics.agent_skill_counts,
    }