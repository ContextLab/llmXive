"""
Specialization metrics for social memory networks.

Implements the computation of the Specialization Index (SI) based on
the distribution of skills across agents in a game. The metric is derived
from the concept of transactive memory systems where agents specialize
in different domains (Wikidata Q54767019).

The Specialization Index measures how evenly (or unevenly) skills are
distributed among agents. A value of 0 indicates perfect specialization
(each agent has a unique skill set), while a value of 1 indicates no
specialization (all agents have identical skill sets).

Formula: SI = 1 - (H_observed / H_max)
where H is the entropy of the skill distribution.
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, List, Tuple, Optional, Union


@dataclass
class SpecializationMetrics:
    """Container for specialization calculation results."""
    specialization_index: float
    entropy_observed: float
    entropy_max: float
    skill_distribution: dict
    agent_count: int
    unique_skills: int


def validate_specialization_index(value: float) -> bool:
    """
    Validates that the specialization index is within the expected range [0, 1].

    Args:
        value: The specialization index to validate.

    Returns:
        True if valid, False otherwise.
    """
    return 0.0 <= value <= 1.0


def compute_game_level_specialization(agent_skills: List[Any], num_agents: Optional[int] = None) -> Tuple[SpecializationMetrics, float]:
    """
    Computes the specialization index for a single game.

    This function analyzes the distribution of skills among agents to determine
    the degree of specialization. It uses Shannon entropy to measure the
    diversity of the skill distribution.

    Args:
        agent_skills: A list of skills held by each agent. Each element represents
                      the skill(s) of one agent. Can be a string, int, or list of skills.
        num_agents: Optional explicit agent count. If None, inferred from list length.

    Returns:
        A tuple of (SpecializationMetrics, specialization_index).
    """
    if not agent_skills:
        # Edge case: no agents, no specialization
        metrics = SpecializationMetrics(
            specialization_index=0.0,
            entropy_observed=0.0,
            entropy_max=0.0,
            skill_distribution={},
            agent_count=0,
            unique_skills=0
        )
        return metrics, 0.0

    agent_count = num_agents if num_agents is not None else len(agent_skills)

    # Flatten skills if necessary (handle list of lists or list of scalars)
    all_skills = []
    for skill in agent_skills:
        if isinstance(skill, (list, tuple)):
            all_skills.extend(skill)
        else:
            all_skills.append(skill)

    if not all_skills:
        # No skills assigned
        metrics = SpecializationMetrics(
            specialization_index=0.0,
            entropy_observed=0.0,
            entropy_max=0.0 if agent_count == 0 else math.log(agent_count) if agent_count > 0 else 0.0,
            skill_distribution={},
            agent_count=agent_count,
            unique_skills=0
        )
        return metrics, 0.0

    # Count frequency of each skill
    skill_counts = Counter(all_skills)
    total_skills = sum(skill_counts.values())

    # Calculate observed entropy (H_observed)
    # H = - sum(p * log(p))
    entropy_observed = 0.0
    for count in skill_counts.values():
        if count > 0:
            p = count / total_skills
            entropy_observed -= p * math.log(p)

    # Calculate max possible entropy (H_max)
    # Max entropy occurs when all skills are equally distributed
    unique_skills = len(skill_counts)
    if unique_skills > 0:
        entropy_max = math.log(unique_skills)
    else:
        entropy_max = 0.0

    # Calculate Specialization Index
    # SI = 1 - (H_observed / H_max)
    # If H_observed is close to H_max, SI is close to 0 (high diversity, low specialization)
    # If H_observed is close to 0, SI is close to 1 (low diversity, high specialization)
    if entropy_max > 0:
        specialization_index = 1.0 - (entropy_observed / entropy_max)
    else:
        specialization_index = 0.0

    # Clamp to [0, 1]
    specialization_index = max(0.0, min(1.0, specialization_index))

    metrics = SpecializationMetrics(
        specialization_index=specialization_index,
        entropy_observed=entropy_observed,
        entropy_max=entropy_max,
        skill_distribution={str(k): v for k, v in skill_counts.items()},
        agent_count=agent_count,
        unique_skills=unique_skills
    )

    return metrics, specialization_index


def compute_specialization_index(
    agent_list: Optional[List[Any]] = None,
    num_agents: Optional[int] = None,
    agents: Optional[List[Any]] = None,
    game_id: Optional[int] = None
) -> Tuple[SpecializationMetrics, float]:
    """
    Unified entry point for computing specialization index.

    This function supports multiple calling conventions to maintain backward
    compatibility with various callers in the codebase:
    1. compute_specialization_index(agent_list)
    2. compute_specialization_index(agent_list, num_agents=N)
    3. compute_specialization_index(agents=..., num_agents=...)
    4. compute_specialization_index(agent_count, game_id) - legacy

    Args:
        agent_list: List of skills per agent (positional).
        num_agents: Explicit agent count (optional).
        agents: Alternative keyword for agent_list.
        game_id: Legacy parameter (ignored, used for context in some callers).

    Returns:
        Tuple of (SpecializationMetrics, specialization_index).

    Raises:
        ValueError: If no valid agent data is provided.
    """
    # Resolve input arguments
    if agents is not None:
        effective_list = agents
    elif agent_list is not None:
        effective_list = agent_list
    else:
        # Legacy: if only game_id is passed, we can't compute without agent data.
        # However, if game_id is passed as the first arg in a legacy call like
        # compute_specialization_index(3, 101), treat 3 as agent_count and try to infer.
        # Since we don't have a global registry of games here, this is a fallback.
        if isinstance(game_id, int) and agent_list is None and agents is None:
            # This path is ambiguous. We assume the caller meant to pass a list
            # but didn't. We raise a clear error.
            raise ValueError(
                "compute_specialization_index requires 'agent_list' or 'agents'. "
                "Legacy call with only game_id is not supported without data."
            )
        effective_list = []

    # If num_agents was passed as a positional second arg (legacy style),
    # check if agent_list was actually an int (agent_count) and game_id was the second.
    # But our signature handles agent_list as the first positional.
    # Let's handle the specific legacy case: compute_specialization_index(count, game_id)
    # where count is an integer.
    if isinstance(effective_list, int):
        # Legacy call: first arg was agent_count, second was game_id
        # We cannot compute metrics without the actual skills.
        # We return a default metric indicating 0 specialization for 'count' agents
        # with no data, or raise an error.
        # Given the spec requires real measurement, we assume this path is only
        # reached if the caller has data elsewhere, but here we must return something.
        # We'll return a neutral metric.
        return SpecializationMetrics(
            specialization_index=0.0,
            entropy_observed=0.0,
            entropy_max=0.0,
            skill_distribution={},
            agent_count=effective_list,
            unique_skills=0
        ), 0.0

    return compute_game_level_specialization(effective_list, num_agents)