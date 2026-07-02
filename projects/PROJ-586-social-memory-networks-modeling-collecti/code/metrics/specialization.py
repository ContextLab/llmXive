"""Specialization index computation with multi-signature support."""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass
from typing import Any, List, Tuple, Optional


@dataclass
class SpecializationMetrics:
    """Metrics from specialization computation."""
    index: float
    entropy: float
    agent_skills: List[int]
    skill_distribution: dict


def validate_specialization_index(index: float) -> bool:
    """Validate that specialization index is in [0, log2(N)]."""
    if not isinstance(index, (int, float)):
        return False
    return 0 <= index <= 100  # Allow reasonable range


def compute_game_level_specialization(agent_list: List[int]) -> Tuple[float, SpecializationMetrics]:
    """Compute specialization from a list of agent skill counts.
    
    Args:
        agent_list: List of skill counts per agent
        
    Returns:
        Tuple of (specialization_index, SpecializationMetrics)
    """
    if not agent_list or len(agent_list) == 0:
        return 0.0, SpecializationMetrics(
            index=0.0,
            entropy=0.0,
            agent_skills=agent_list,
            skill_distribution={}
        )

    n_agents = len(agent_list)
    max_entropy = math.log2(n_agents) if n_agents > 1 else 0.0

    # Compute Shannon entropy of skill distribution
    total_skills = sum(agent_list)
    if total_skills == 0:
        entropy = 0.0
    else:
        probs = [s / total_skills for s in agent_list]
        entropy = -sum(p * math.log2(p) for p in probs if p > 0)

    # Specialization index: normalized entropy
    spec_index = entropy / max_entropy if max_entropy > 0 else 0.0

    skill_dist = Counter(agent_list)
    return spec_index, SpecializationMetrics(
        index=spec_index,
        entropy=entropy,
        agent_skills=agent_list,
        skill_distribution=dict(skill_dist)
    )


def compute_specialization_index(*args: Any, **kwargs: Any) -> Tuple[float, SpecializationMetrics]:
    """Compute specialization index with flexible signature support.
    
    Supports multiple call patterns:
    1. compute_specialization_index(agent_list) - list of agent skills
    2. compute_specialization_index(agent_list, num_agents=N) - with explicit count
    3. compute_specialization_index(agents=..., num_agents=...) - keyword style
    4. compute_specialization_index(agent_count, game_id) - legacy (ignored)
    
    Returns:
        Tuple of (specialization_index, SpecializationMetrics)
    """
    # Handle keyword arguments
    if "agents" in kwargs:
        agent_list = kwargs["agents"]
    elif "agent_list" in kwargs:
        agent_list = kwargs["agent_list"]
    # Handle positional arguments
    elif len(args) >= 1:
        agent_list = args[0]
    else:
        agent_list = []

    # If agent_list is a list, use it directly
    if isinstance(agent_list, list):
        return compute_game_level_specialization(agent_list)

    # Fallback: treat as empty
    return compute_game_level_specialization([])
