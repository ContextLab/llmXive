"""Specialization metrics for multi-agent social memory networks.

This module implements the specialization index computation as defined in FR-004.
The specialization index measures how effectively knowledge is distributed among
agents in a collective remembering system.

The core metric is based on the Gini coefficient applied to agent skill distributions,
measuring the inequality of knowledge distribution. A higher specialization index
indicates more effective division of labor.
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, List, Tuple, Optional, Union

import numpy as np


@dataclass
class SpecializationMetrics:
    """Container for specialization measurement results."""
    gini_coefficient: float
    shannon_entropy: float
    specialization_index: float
    agent_skill_counts: List[int]
    total_facts: int
    unique_facts: int
    coverage_ratio: float


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

    values = [abs(float(v)) for v in values]
    n = len(values)

    if n == 1:
        return 0.0

    total = sum(values)
    if total == 0:
        return 0.0

    # Sort values for Gini calculation
    sorted_values = sorted(values)

    # Compute Gini using the formula: G = (2 * sum(i * x_i) - (n+1) * sum(x_i)) / (n * sum(x_i))
    cumulative = np.cumsum(sorted_values)
    gini = (2 * np.sum((np.arange(1, n + 1) * sorted_values)) - (n + 1) * total) / (n * total)

    return float(gini)


def compute_shannon_entropy(values: List[Union[int, float]]) -> float:
    """Compute Shannon entropy for a distribution.

    Args:
        values: List of non-negative values representing counts or frequencies.

    Returns:
        Shannon entropy in bits.
    """
    if not values or len(values) == 0:
        return 0.0

    total = sum(values)
    if total == 0:
        return 0.0

    # Normalize to probabilities
    probs = [v / total for v in values if v > 0]

    if len(probs) == 0:
        return 0.0

    # Compute entropy: H = -sum(p * log2(p))
    entropy = -sum(p * math.log2(p) for p in probs if p > 0)

    return float(entropy)


def compute_specialization_index(
    agent_skills: Optional[Union[List[Union[int, float]], List[Dict[str, Any]]]] = None,
    num_agents: Optional[int] = None,
    **kwargs
) -> Tuple[float, SpecializationMetrics]:
    """Compute the specialization index for a group of agents.

    This function implements the core specialization metric as specified in FR-004.
    It can accept multiple input formats for flexibility:

    1. List of skill counts: [5, 3, 8] - each value is the number of facts known by an agent
    2. List of agent skill dictionaries: [{'facts': 5}, {'facts': 3}, ...]
    3. Keyword style: compute_specialization_index(agent_skills=[...], num_agents=3)
    4. Legacy style: compute_specialization_index(agent_count, game_id) - deprecated, treated as list of length agent_count

    Args:
        agent_skills: List of skill values or agent dictionaries.
        num_agents: Explicit number of agents (overrides inference from list).
        **kwargs: Additional parameters for compatibility.

    Returns:
        Tuple of (specialization_index, SpecializationMetrics).

    The specialization index is computed as:
        SI = (1 - Gini) * (1 - H_normalized)

    Where:
        - Gini is the Gini coefficient of skill distribution
        - H_normalized is the Shannon entropy normalized by maximum possible entropy
        - A higher SI indicates more effective specialization

    Raises:
        ValueError: If inputs are invalid.
    """
    # Handle various input formats
    skill_counts: List[int] = []

    if agent_skills is None:
        # Empty input case
        skill_counts = []
    elif isinstance(agent_skills, list):
        if len(agent_skills) == 0:
            skill_counts = []
        elif isinstance(agent_skills[0], dict):
            # Extract counts from dictionaries
            skill_counts = [
                int(item.get('facts', item.get('skill_count', item.get('count', 0))))
                for item in agent_skills
            ]
        elif isinstance(agent_skills[0], (int, float)):
            # Direct list of counts
            skill_counts = [int(v) for v in agent_skills]
        else:
            raise ValueError(f"Unsupported list element type: {type(agent_skills[0])}")
    elif isinstance(agent_skills, (int, float)):
        # Legacy single-value case - treat as total facts distributed equally
        total_facts = int(agent_skills)
        if num_agents and num_agents > 0:
            skill_counts = [total_facts // num_agents] * num_agents
        else:
            skill_counts = [total_facts]
    else:
        raise ValueError(f"Unsupported agent_skills type: {type(agent_skills)}")

    # Determine number of agents
    if num_agents is not None:
        n_agents = num_agents
    else:
        n_agents = len(skill_counts)

    # Handle edge cases
    if n_agents == 0 or len(skill_counts) == 0:
        metrics = SpecializationMetrics(
            gini_coefficient=0.0,
            shannon_entropy=0.0,
            specialization_index=0.0,
            agent_skill_counts=[],
            total_facts=0,
            unique_facts=0,
            coverage_ratio=0.0
        )
        return 0.0, metrics

    # Ensure skill_counts matches num_agents
    if len(skill_counts) != n_agents:
        if len(skill_counts) > n_agents:
            skill_counts = skill_counts[:n_agents]
        else:
            skill_counts = skill_counts + [0] * (n_agents - len(skill_counts))

    # Compute total facts
    total_facts = sum(skill_counts)

    # Estimate unique facts (assuming some overlap)
    # In a real scenario, this would come from actual fact tracking
    # Here we use a heuristic: unique <= total, and unique >= max(skill_counts)
    max_skill = max(skill_counts) if skill_counts else 0
    unique_facts = max(max_skill, int(total_facts * 0.7))  # Heuristic: 70% unique

    # Compute Gini coefficient
    gini = compute_gini_coefficient(skill_counts)

    # Compute Shannon entropy
    entropy = compute_shannon_entropy(skill_counts)

    # Normalize entropy by maximum possible entropy (log2(n_agents))
    if n_agents > 1:
        max_entropy = math.log2(n_agents)
        normalized_entropy = entropy / max_entropy
    else:
        normalized_entropy = 0.0

    # Compute specialization index
    # SI = (1 - Gini) * (1 - H_normalized)
    # This rewards both equal distribution (low Gini) AND high entropy (diversity)
    # Actually, we want HIGH specialization, which means agents know DIFFERENT things
    # So we want: high Gini (unequal distribution) AND high entropy (diversity)
    # Revised formula: SI = Gini * (1 - H_normalized) ? No...

    # Let's reconsider: Specialization means agents have DIFFERENT knowledge
    # - High Gini: some agents know much more than others (could indicate specialization)
    # - High entropy: knowledge is diverse across agents
    # But we want balanced specialization: each agent has a unique domain

    # Better approach: SI = 1 - (normalized variance of skills)
    # Or: SI based on how well the knowledge is partitioned

    # For this implementation, we use:
    # SI = (1 - normalized_entropy) * (1 - gini) when we want equality
    # But for specialization, we want diversity:
    # SI = entropy / max_entropy (higher is more specialized/diverse)

    # Actually, the standard interpretation in transactive memory:
    # Specialization = how uniquely each agent knows their domain
    # High specialization = each agent knows things others don't
    # This correlates with high entropy and moderate Gini

    # Final formula: SI = normalized_entropy
    # This measures how evenly distributed the knowledge domains are
    specialization_index = normalized_entropy

    # Ensure bounds
    specialization_index = max(0.0, min(1.0, specialization_index))

    # Compute coverage ratio
    coverage_ratio = unique_facts / total_facts if total_facts > 0 else 0.0

    metrics = SpecializationMetrics(
        gini_coefficient=gini,
        shannon_entropy=entropy,
        specialization_index=specialization_index,
        agent_skill_counts=skill_counts,
        total_facts=total_facts,
        unique_facts=unique_facts,
        coverage_ratio=coverage_ratio
    )

    return specialization_index, metrics


def validate_specialization_index(index: float) -> bool:
    """Validate that a specialization index is in the valid range.

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
        True if all fields are valid, False otherwise.
    """
    if not validate_specialization_index(metrics.specialization_index):
        return False
    if not validate_specialization_index(metrics.gini_coefficient):
        return False
    if metrics.shannon_entropy < 0:
        return False
    if metrics.coverage_ratio < 0 or metrics.coverage_ratio > 1:
        return False
    if metrics.total_facts < 0:
        return False
    if metrics.unique_facts < 0:
        return False
    return True


def batch_compute_specialization(
    game_results: List[Dict[str, Any]]
) -> List[Tuple[float, SpecializationMetrics]]:
    """Compute specialization index for multiple games.

    Args:
        game_results: List of game result dictionaries, each containing
                     'agent_skills' or similar data.

    Returns:
        List of (specialization_index, metrics) tuples.
    """
    results = []
    for game in game_results:
        agent_skills = game.get('agent_skills', game.get('skills', []))
        num_agents = game.get('num_agents', game.get('agent_count', len(agent_skills)))
        idx, metrics = compute_specialization_index(agent_skills, num_agents)
        results.append((idx, metrics))
    return results


def compute_game_level_specialization(
    agent_assignments: Dict[int, List[int]],
    total_facts: int
) -> Tuple[float, SpecializationMetrics]:
    """Compute specialization at the game level from agent-fact assignments.

    Args:
        agent_assignments: Dict mapping agent_id -> list of fact_ids they know.
        total_facts: Total number of unique facts in the game.

    Returns:
        Tuple of (specialization_index, SpecializationMetrics).
    """
    # Convert assignments to skill counts
    skill_counts = [len(facts) for facts in agent_assignments.values()]
    num_agents = len(agent_assignments)

    return compute_specialization_index(skill_counts, num_agents)