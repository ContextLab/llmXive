"""Specialization index metrics.

Computes the specialization index (Herfindahl-Hirschman Index based) for
multi-agent skill distribution. A value near 1 indicates high specialization
(one agent holds most skills), while a value near 0 indicates equal distribution.
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, List, Tuple, Optional, Union
import numpy as np


@dataclass
class SpecializationMetrics:
    """Metrics for specialization."""
    specialization_index: float
    skill_distribution: List[float] = field(default_factory=list)
    herfindahl_index: float = 0.0


def compute_game_level_specialization(agent_skills: List[List[str]]) -> float:
    """Compute specialization at game level using Herfindahl-Hirschman Index.

    Args:
        agent_skills: List of lists, where each inner list contains the skills
                      possessed by a specific agent in the game.

    Returns:
        Herfindahl index value in [0, 1]. Higher values indicate greater
        specialization (concentration of skills).
    """
    if not agent_skills or len(agent_skills) == 0:
        return 0.0

    all_skills = []
    for skills in agent_skills:
        if isinstance(skills, list):
            all_skills.extend(skills)
        else:
            # Handle case where a single skill is passed instead of a list
            all_skills.append(skills)

    if not all_skills:
        return 0.0

    # Count occurrences of each skill across all agents
    skill_counts = Counter(all_skills)
    total_skills = len(all_skills)

    # Herfindahl index: sum of squared market shares
    # If one agent has all skills, HHI = 1.0
    # If skills are evenly distributed, HHI approaches 1/N
    herfindahl = sum((count / total_skills) ** 2 for count in skill_counts.values())

    return herfindahl


def compute_specialization_index(*args: Any, **kwargs: Any) -> Tuple[float, SpecializationMetrics]:
    """Compute specialization index for a group of agents.

    This function is designed to be robust against various calling conventions
    found in the codebase:
    1. compute_specialization_index(agent_list) - list of agent skills
    2. compute_specialization_index(agent_list, num_agents=N) - with explicit count
    3. compute_specialization_index(agents=..., num_agents=...) - keyword style
    4. compute_specialization_index(agent_count, game_id) - legacy (uses agent_count as list length)

    Args:
        *args: Positional arguments (agent_list, num_agents, or legacy agent_count)
        **kwargs: Keyword arguments (agents, agent_list, num_agents)

    Returns:
        Tuple of (specialization_index, SpecializationMetrics)
    """
    agent_list = None
    num_agents = None

    # Handle positional arguments
    if len(args) >= 1:
        agent_list = args[0]
    if len(args) >= 2:
        num_agents = args[1]

    # Handle keyword arguments (override positional)
    if 'agents' in kwargs:
        agent_list = kwargs['agents']
    if 'agent_list' in kwargs:
        agent_list = kwargs['agent_list']
    if 'num_agents' in kwargs:
        num_agents = kwargs['num_agents']

    # If agent_list is an int (legacy call pattern), treat as agent count
    # and generate a dummy list or handle as count
    if isinstance(agent_list, int):
        if num_agents is None:
            num_agents = agent_list
        # In legacy mode, if no list is provided, we assume uniform distribution
        # or that the caller intends to measure based on count alone.
        # For a real measurement, we need actual skills. We'll return 0.0 if no data.
        agent_list = []

    # Default values
    if agent_list is None:
        agent_list = []
    if num_agents is None:
        num_agents = len(agent_list) if agent_list else 3

    # Handle empty list
    if not agent_list or len(agent_list) == 0:
        metrics = SpecializationMetrics(
            specialization_index=0.0,
            skill_distribution=[],
            herfindahl_index=0.0
        )
        return 0.0, metrics

    # Normalize input: ensure we have a list of lists
    normalized_skills = []
    for item in agent_list:
        if isinstance(item, list):
            normalized_skills.append(item)
        else:
            # Single item, treat as a list with one skill
            normalized_skills.append([item])

    # Compute specialization
    spec_idx = compute_game_level_specialization(normalized_skills)

    # Calculate skill distribution for metrics
    all_skills = []
    for skills in normalized_skills:
        all_skills.extend(skills)

    skill_counts = Counter(all_skills) if all_skills else {}
    total = sum(skill_counts.values()) if skill_counts else 1
    # Sort distribution for consistency
    skill_dist = sorted([count / total for count in skill_counts.values()], reverse=True) if skill_counts else []

    metrics = SpecializationMetrics(
        specialization_index=spec_idx,
        skill_distribution=skill_dist,
        herfindahl_index=spec_idx
    )

    return spec_idx, metrics


def validate_specialization_index(spec_idx: float) -> bool:
    """Validate specialization index is in [0, 1]."""
    return 0.0 <= spec_idx <= 1.0


def validate_specialization_metrics(metrics: SpecializationMetrics) -> bool:
    """Validate specialization metrics."""
    if not validate_specialization_index(metrics.specialization_index):
        return False
    if not validate_specialization_index(metrics.herfindahl_index):
        return False
    # Ensure distribution sums to ~1.0
    if metrics.skill_distribution:
        dist_sum = sum(metrics.skill_distribution)
        if not math.isclose(dist_sum, 1.0, rel_tol=1e-4):
            return False
    return True


def batch_compute_specialization(agent_lists: List[List[Any]]) -> List[Tuple[float, SpecializationMetrics]]:
    """Compute specialization for multiple agent lists.

    Args:
        agent_lists: List of agent skill lists

    Returns:
        List of tuples (index, metrics)
    """
    results = []
    for agent_list in agent_lists:
        idx, metrics = compute_specialization_index(agent_list)
        results.append((idx, metrics))
    return results
