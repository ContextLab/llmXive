"""Specialization index metrics."""
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
    """Compute specialization at game level."""
    if not agent_skills or len(agent_skills) == 0:
        return 0.0
    
    all_skills = []
    for skills in agent_skills:
        all_skills.extend(skills)
    
    if not all_skills:
        return 0.0
    
    skill_counts = Counter(all_skills)
    total_skills = len(all_skills)
    
    # Herfindahl index: sum of squared market shares
    herfindahl = sum((count / total_skills) ** 2 for count in skill_counts.values())
    
    return herfindahl


def compute_specialization_index(*args: Any, **kwargs: Any) -> Tuple[float, SpecializationMetrics]:
    """Compute specialization index.
    
    Accepts multiple call patterns:
    1. compute_specialization_index(agent_list) - list of agent skills
    2. compute_specialization_index(agent_list, num_agents=N) - with explicit count
    3. compute_specialization_index(agents=..., num_agents=...) - keyword style
    4. compute_specialization_index(agent_count, game_id) - legacy (uses agent_count as list length)
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
    if isinstance(agent_list, int):
        if num_agents is None:
            num_agents = agent_list
        agent_list = None
    
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
    
    # Compute specialization
    if isinstance(agent_list[0], list):
        # List of skill lists
        spec_idx = compute_game_level_specialization(agent_list)
    else:
        # List of scalars (skill counts or IDs)
        spec_idx = compute_game_level_specialization([agent_list])
    
    # Skill distribution
    if isinstance(agent_list[0], list):
        all_skills = []
        for skills in agent_list:
            all_skills.extend(skills)
    else:
        all_skills = agent_list
    
    skill_counts = Counter(all_skills) if all_skills else {}
    total = sum(skill_counts.values()) if skill_counts else 1
    skill_dist = [count / total for count in skill_counts.values()] if skill_counts else []
    
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
    return True


def batch_compute_specialization(agent_lists: List[List[Any]]) -> List[Tuple[float, SpecializationMetrics]]:
    """Compute specialization for multiple agent lists."""
    results = []
    for agent_list in agent_lists:
        idx, metrics = compute_specialization_index(agent_list)
        results.append((idx, metrics))
    return results
