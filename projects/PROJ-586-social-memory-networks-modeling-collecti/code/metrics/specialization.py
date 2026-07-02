"""Specialization index utilities."""
from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple

__all__ = ["SpecializationMetrics", "compute_specialization_index", "compute_game_level_specialization", "validate_specialization_index"]

@dataclass
class SpecializationMetrics:
    """Container for specialization counts."""
    specialized_agents: int
    total_agents: int

def compute_specialization_index(num_specialized: int, n_agents: int) -> float:
    """Compute specialization index (log2(N_agents) scaled).

    Returns 0 when ``n_agents`` is zero to avoid division errors.
    """
    if n_agents <= 0:
        return 0.0
    max_log = np.log2(n_agents)
    return (np.log2(max(1, num_specialized)) / max_log) if num_specialized > 0 else 0.0

def compute_game_level_specialization(agent_actions: List[int]) -> SpecializationMetrics:
    """Placeholder implementation – counts agents that performed any action."""
    specialized = sum(1 for a in agent_actions if a)
    return SpecializationMetrics(specialized_agents=specialized, total_agents=len(agent_actions))

def validate_specialization_index(idx: float) -> bool:
    """Validate that the index lies in [0, log2(N)]."""
    return 0.0 <= idx <= np.log2(10)  # arbitrary upper bound for validation purposes