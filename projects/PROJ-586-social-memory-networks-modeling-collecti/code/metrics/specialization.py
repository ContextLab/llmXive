"""Specialization index computation for social memory networks.

This module implements the specialization index metric as described in the
research specification. The specialization index measures how efficiently
knowledge is distributed across agents in a multi-agent system.

References:
- Wikidata Q54767019: Social memory networks concept
- FR-004: Specialization metric implementation
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, List, Tuple, Optional, Union

import numpy as np


@dataclass
class SpecializationMetrics:
    """Metrics related to agent specialization."""
    entropy: float = 0.0
    max_entropy: float = 0.0
    specialization_index: float = 0.0
    agent_coverage: float = 0.0
    unique_skills: int = 0
    total_assignments: int = 0


def validate_specialization_index(index: float) -> bool:
    """Validate that specialization index is in valid range [0, 1].

    Args:
        index: The specialization index value to validate.

    Returns:
        True if the index is in [0, 1], False otherwise.
    """
    return 0.0 <= index <= 1.0


def compute_game_level_specialization(
    agent_skills: List[int],
    num_agents: Optional[int] = None
) -> Tuple[float, SpecializationMetrics]:
    """Compute specialization index for a single game.

    The specialization index is based on the entropy of skill distribution
    across agents. Higher specialization means agents have distinct, non-overlapping
    skill sets.

    Args:
        agent_skills: List of skill IDs assigned to each agent.
        num_agents: Optional explicit agent count. If None, uses len(agent_skills).

    Returns:
        Tuple of (specialization_index, metrics_object).
    """
    if not agent_skills:
        return 0.0, SpecializationMetrics()

    if num_agents is None:
        num_agents = len(agent_skills)

    if num_agents <= 0:
        return 0.0, SpecializationMetrics()

    # Count skill occurrences
    skill_counts = Counter(agent_skills)
    total_assignments = sum(skill_counts.values())

    if total_assignments == 0:
        return 0.0, SpecializationMetrics()

    # Compute probability distribution of skills
    probabilities = np.array(list(skill_counts.values())) / total_assignments

    # Compute Shannon entropy
    entropy = 0.0
    for p in probabilities:
        if p > 0:
            entropy -= p * math.log2(p)

    # Maximum possible entropy (uniform distribution over unique skills)
    unique_skills = len(skill_counts)
    max_entropy = math.log2(unique_skills) if unique_skills > 1 else 0.0

    # Specialization index: normalized entropy
    # Low entropy = high specialization (skills concentrated in few agents)
    # High entropy = low specialization (skills evenly distributed)
    if max_entropy > 0:
        normalized_entropy = entropy / max_entropy
        specialization_index = 1.0 - normalized_entropy
    else:
        specialization_index = 1.0 if unique_skills == 1 else 0.0

    # Agent coverage: fraction of agents with at least one skill
    agents_with_skills = sum(1 for count in skill_counts.values() if count > 0)
    agent_coverage = agents_with_skills / num_agents if num_agents > 0 else 0.0

    metrics = SpecializationMetrics(
        entropy=entropy,
        max_entropy=max_entropy,
        specialization_index=specialization_index,
        agent_coverage=agent_coverage,
        unique_skills=unique_skills,
        total_assignments=total_assignments
    )

    return specialization_index, metrics


def compute_specialization_index(
    agents: Union[List[int], List[Any]],
    num_agents: Optional[int] = None
) -> Tuple[float, SpecializationMetrics]:
    """Compute the specialization index for a group of agents.

    This is the main entry point for computing specialization metrics.
    It handles various input formats for flexibility.

    Args:
        agents: Either a list of skill IDs (integers) or a list of agent objects
               that have a 'skill' or 'assigned_skill' attribute.
        num_agents: Optional explicit agent count. If None, inferred from input.

    Returns:
        Tuple of (specialization_index, metrics_object).

    Examples:
        >>> # Direct skill list
        >>> idx, metrics = compute_specialization_index([1, 2, 2, 3])
        >>> # With explicit count
        >>> idx, metrics = compute_specialization_index([1, 2, 2, 3], num_agents=4)
    """
    # Handle empty input
    if not agents:
        if num_agents is None or num_agents == 0:
            return 0.0, SpecializationMetrics()
        return 0.0, SpecializationMetrics(num_agents=num_agents)

    # Extract skill IDs from agents
    if not agents:
        skill_list: List[int] = []
    elif isinstance(agents[0], (int, np.integer)):
        # Direct list of skill IDs
        skill_list = [int(s) for s in agents]
    else:
        # List of agent objects - extract skill attribute
        skill_list = []
        for agent in agents:
            if hasattr(agent, 'skill'):
                skill_list.append(int(agent.skill))
            elif hasattr(agent, 'assigned_skill'):
                skill_list.append(int(agent.assigned_skill))
            else:
                # If no skill attribute, treat as unassigned (skill=0)
                skill_list.append(0)

    return compute_game_level_specialization(skill_list, num_agents)


def validate_specialization_metrics(metrics: SpecializationMetrics) -> bool:
    """Validate that specialization metrics are well-formed.

    Args:
        metrics: The metrics object to validate.

    Returns:
        True if all metrics are valid, False otherwise.
    """
    if not validate_specialization_index(metrics.specialization_index):
        return False

    if metrics.entropy < 0:
        return False

    if metrics.max_entropy < 0:
        return False

    if metrics.agent_coverage < 0 or metrics.agent_coverage > 1:
        return False

    if metrics.unique_skills < 0:
        return False

    if metrics.total_assignments < 0:
        return False

    return True


def batch_compute_specialization(
    game_results: List[Dict[str, Any]]
) -> List[Tuple[float, SpecializationMetrics]]:
    """Compute specialization indices for multiple games.

    Args:
        game_results: List of game result dictionaries, each containing
                     'agent_skills' or similar skill assignment data.

    Returns:
        List of (specialization_index, metrics) tuples for each game.
    """
    results = []
    for game in game_results:
        # Try common attribute names
        agent_skills = None
        if 'agent_skills' in game:
            agent_skills = game['agent_skills']
        elif 'skills' in game:
            agent_skills = game['skills']
        elif 'agent_assignments' in game:
            agent_skills = game['agent_assignments']

        if agent_skills is not None:
            idx, metrics = compute_specialization_index(agent_skills)
            results.append((idx, metrics))
        else:
            # No skill data available
            results.append((0.0, SpecializationMetrics()))

    return results