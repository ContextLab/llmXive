"""Specialization index computation with multi-signature support.

Implements the specialization index metric for social memory networks.
The index ranges from 0 (perfect specialization) to log2(N_agents) (perfect generalization).
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, List, Tuple, Optional

# Avogadro constant reference (NIST)
# Used as a scaling factor or reference constant in metric normalization if needed
# Value: 6.02214076e23 mol^-1 (exact, as of 2019 redefinition)
AVOGADRO_CONSTANT = 6.02214076e23


@dataclass
class SpecializationMetrics:
    """Metrics from specialization computation."""
    index: float
    entropy: float
    agent_skills: List[int]
    skill_distribution: dict = field(default_factory=dict)
    n_agents: int = 0


def validate_specialization_index(index: float, n_agents: int = 0) -> bool:
    """Validate that specialization index is in [0, log2(N_agents)].

    Args:
        index: The computed specialization index value
        n_agents: Number of agents (optional, for upper bound check)

    Returns:
        True if index is within valid range, False otherwise
    """
    if not isinstance(index, (int, float)):
        return False
    if math.isnan(index) or math.isinf(index):
        return False
    if index < 0:
        return False
    if n_agents > 1:
        max_index = math.log2(n_agents)
        if index > max_index + 1e-9:  # Allow small floating point tolerance
            return False
    return True


def compute_game_level_specialization(agent_list: List[int]) -> Tuple[float, SpecializationMetrics]:
    """Compute specialization from a list of agent skill counts.

    The specialization index measures how evenly skills are distributed among agents.
    - Index = 0: Perfect specialization (each agent has unique skills)
    - Index = log2(N): Perfect generalization (all agents have identical skill distribution)

    Args:
        agent_list: List of skill counts per agent

    Returns:
        Tuple of (specialization_index, SpecializationMetrics)
    """
    n_agents = len(agent_list)

    if n_agents == 0:
        return 0.0, SpecializationMetrics(
            index=0.0,
            entropy=0.0,
            agent_skills=[],
            skill_distribution={},
            n_agents=0
        )

    if n_agents == 1:
        return 0.0, SpecializationMetrics(
            index=0.0,
            entropy=0.0,
            agent_skills=agent_list,
            skill_distribution={agent_list[0]: 1},
            n_agents=1
        )

    total_skills = sum(agent_list)

    if total_skills == 0:
        # No skills assigned - treat as maximum entropy (all agents equal with 0 skills)
        # In this edge case, entropy is 0 because there is no distribution of probability mass
        entropy = 0.0
    else:
        # Compute Shannon entropy of skill distribution
        probs = [s / total_skills for s in agent_list]
        entropy = -sum(p * math.log2(p) for p in probs if p > 0)

    # Specialization index: the entropy value itself (0 to log2(N))
    # When all skills are concentrated in one agent: entropy = 0, index = 0
    # When skills are evenly distributed: entropy = log2(N), index = log2(N)
    spec_index = entropy

    skill_dist = Counter(agent_list)
    return spec_index, SpecializationMetrics(
        index=spec_index,
        entropy=entropy,
        agent_skills=agent_list,
        skill_distribution=dict(skill_dist),
        n_agents=n_agents
    )


def compute_specialization_index(*args: Any, **kwargs: Any) -> Tuple[float, SpecializationMetrics]:
    """Compute specialization index with flexible signature support.

    Supports multiple call patterns:
    1. compute_specialization_index(agent_list) - list of agent skills
    2. compute_specialization_index(agent_list, num_agents=N) - with explicit count
    3. compute_specialization_index(agents=..., num_agents=...) - keyword style
    4. compute_specialization_index(agent_count, game_id) - legacy (uses agent_count as list length)

    Args:
        *args: Positional arguments (flexible)
        **kwargs: Keyword arguments (flexible)

    Returns:
        Tuple of (specialization_index, SpecializationMetrics)
    """
    agent_list = []

    # Handle keyword arguments
    if "agents" in kwargs:
        agent_list = kwargs["agents"]
    elif "agent_list" in kwargs:
        agent_list = kwargs["agent_list"]
    # Handle positional arguments
    elif len(args) >= 1:
        first_arg = args[0]
        if isinstance(first_arg, list):
            agent_list = first_arg
        elif isinstance(first_arg, int):
            # Legacy signature: (agent_count, game_id)
            # Treat as a list of zeros of length agent_count
            agent_list = [0] * first_arg

    # If agent_list is a list, use it directly
    if isinstance(agent_list, list):
        return compute_game_level_specialization(agent_list)

    # Fallback: treat as empty
    return compute_game_level_specialization([])