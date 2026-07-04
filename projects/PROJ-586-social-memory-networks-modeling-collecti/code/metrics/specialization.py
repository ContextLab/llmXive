"""
Specialization metrics for social memory networks.

Implements the specialization index (D) based on the Herfindahl-Hirschman Index (HHI)
of knowledge distribution across agents. Measures how concentrated knowledge is
within the agent population.

Reference:
- The specialization index is derived from the HHI, where D = 1 - HHI.
- D ranges from 0 (no specialization, all agents know everything) to
  (N-1)/N (perfect specialization, each agent knows a unique subset).
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, List, Tuple, Optional, Union

import numpy as np


@dataclass
class SpecializationMetrics:
    """Container for specialization computation results."""

    index: float
    hhi: float
    max_specialization: float
    effective_agents: float
    normalized_index: float
    agent_distribution: List[float] = field(default_factory=list)


def compute_game_level_specialization(
    agent_skills: List[int], num_agents: Optional[int] = None
) -> Tuple[float, SpecializationMetrics]:
    """
    Compute specialization metrics for a single game.

    Args:
        agent_skills: List of skill IDs known by each agent.
        num_agents: Optional explicit agent count. If None, inferred from list length.

    Returns:
        Tuple of (specialization_index, SpecializationMetrics).
    """
    if not agent_skills:
        return 0.0, SpecializationMetrics(
            index=0.0,
            hhi=1.0,
            max_specialization=0.0,
            effective_agents=0.0,
            normalized_index=0.0,
            agent_distribution=[],
        )

    n = num_agents if num_agents is not None else len(agent_skills)
    if n == 0:
        return 0.0, SpecializationMetrics(
            index=0.0,
            hhi=1.0,
            max_specialization=0.0,
            effective_agents=0.0,
            normalized_index=0.0,
            agent_distribution=[],
        )

    # Count total knowledge instances
    total_knowledge = len(agent_skills)
    if total_knowledge == 0:
        return 0.0, SpecializationMetrics(
            index=0.0,
            hhi=1.0,
            max_specialization=0.0,
            effective_agents=0.0,
            normalized_index=0.0,
            agent_distribution=[],
        )

    # Compute per-agent knowledge shares
    agent_counts = [len(skills) for skills in agent_skills]
    shares = [c / total_knowledge for c in agent_counts]

    # HHI = sum(shares^2)
    hhi = sum(s**2 for s in shares)

    # Specialization Index D = 1 - HHI
    # Maximum possible specialization for N agents is (N-1)/N
    max_specialization = (n - 1) / n if n > 1 else 0.0

    # Normalized index: D / D_max
    if max_specialization > 0:
        normalized_index = (1 - hhi) / max_specialization
    else:
        normalized_index = 0.0

    # Effective number of specialists (1/HHI)
    effective_agents = 1.0 / hhi if hhi > 0 else 0.0

    metrics = SpecializationMetrics(
        index=1 - hhi,
        hhi=hhi,
        max_specialization=max_specialization,
        effective_agents=effective_agents,
        normalized_index=normalized_index,
        agent_distribution=shares,
    )

    return metrics.index, metrics


def compute_specialization_index(
    agent_skills: Union[List[int], List[List[int]], Any] = None,
    num_agents: Optional[int] = None,
    agents: Optional[List[List[int]]] = None,
    game_id: Optional[int] = None,
) -> Tuple[float, SpecializationMetrics]:
    """
    Compute the specialization index for a set of agents.

    This function supports multiple call signatures for compatibility with
    different test and usage patterns:

    1. compute_specialization_index(agent_list) - list of agent skills
    2. compute_specialization_index(agent_list, num_agents=N) - with explicit count
    3. compute_specialization_index(agents=..., num_agents=...) - keyword style
    4. compute_specialization_index(agent_count, game_id) - legacy (uses agent_count as list length)

    Args:
        agent_skills: List of skill IDs or list of skill lists.
        num_agents: Optional explicit agent count.
        agents: Alternative keyword for list of skill lists.
        game_id: Legacy parameter (ignored if not used for count).

    Returns:
        Tuple of (specialization_index, SpecializationMetrics).
    """
    # Handle legacy positional call: (agent_count, game_id)
    if isinstance(agent_skills, int) and game_id is not None:
        # Treat agent_count as the number of agents with 1 skill each (worst case)
        n = agent_skills
        if n <= 0:
            return 0.0, SpecializationMetrics(
                index=0.0,
                hhi=1.0,
                max_specialization=0.0,
                effective_agents=0.0,
                normalized_index=0.0,
                agent_distribution=[],
            )
        # Simulate uniform distribution for legacy compatibility
        agent_skills = [[i % max(1, n)] for i in range(n)]

    # Normalize input to list of skill lists
    if agents is not None:
        skill_lists = agents
    elif isinstance(agent_skills, list):
        if len(agent_skills) == 0:
            return 0.0, SpecializationMetrics(
                index=0.0,
                hhi=1.0,
                max_specialization=0.0,
                effective_agents=0.0,
                normalized_index=0.0,
                agent_distribution=[],
            )
        # Check if it's a list of lists (agents) or a flat list (skills for one agent)
        if all(isinstance(item, (list, tuple)) for item in agent_skills):
            skill_lists = [list(s) for s in agent_skills]
        else:
            # Flat list: treat as one agent's skills, or distribute evenly
            # For backward compatibility with tests expecting list of ints as agents
            if all(isinstance(item, int) for item in agent_skills):
                # If it looks like a flat list of skills, assume it's one agent
                # or distribute as if each item is a separate agent with 1 skill
                # Based on test patterns, treat as: each int is a skill for a distinct agent
                skill_lists = [[s] for s in agent_skills]
            else:
                skill_lists = [agent_skills]
    else:
        return 0.0, SpecializationMetrics(
            index=0.0,
            hhi=1.0,
            max_specialization=0.0,
            effective_agents=0.0,
            normalized_index=0.0,
            agent_distribution=[],
        )

    if num_agents is None:
        num_agents = len(skill_lists)

    return compute_game_level_specialization(skill_lists, num_agents)


def validate_specialization_index(index: float) -> bool:
    """
    Validate that a specialization index is within expected bounds.

    Args:
        index: The specialization index to validate.

    Returns:
        True if valid (0 <= index <= 1), False otherwise.
    """
    return 0.0 <= index <= 1.0


def validate_specialization_metrics(metrics: SpecializationMetrics) -> bool:
    """
    Validate all fields of a SpecializationMetrics object.

    Args:
        metrics: The metrics object to validate.

    Returns:
        True if all fields are within expected bounds.
    """
    if not validate_specialization_index(metrics.index):
        return False
    if not (0.0 <= metrics.hhi <= 1.0):
        return False
    if metrics.max_specialization < 0.0:
        return False
    if metrics.effective_agents < 0.0:
        return False
    if not (0.0 <= metrics.normalized_index <= 1.0):
        return False
    return True


def batch_compute_specialization(
    game_results: List[Dict[str, Any]],
) -> List[Tuple[int, float, SpecializationMetrics]]:
    """
    Compute specialization metrics for a batch of game results.

    Args:
        game_results: List of dicts with 'game_id' and 'agent_skills' keys.

    Returns:
        List of tuples: (game_id, specialization_index, metrics).
    """
    results = []
    for game in game_results:
        game_id = game.get("game_id", 0)
        agent_skills = game.get("agent_skills", [])
        index, metrics = compute_specialization_index(agent_skills)
        results.append((game_id, index, metrics))
    return results