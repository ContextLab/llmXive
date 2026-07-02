"""Specialization index metric utilities."""
from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple


@dataclass
class SpecializationMetrics:
    specialization_index: int


def compute_specialization_index(
    agent_specializations: List[int],
    num_agents: int,
) -> int:
    """
    Compute the specialization index (0 to log2(N_agents)).

    The index is the ceiling of the binary logarithm of the number of
    distinct specialization groups present among agents.
    """
    if num_agents <= 0:
        raise ValueError("num_agents must be positive")
    distinct = len(set(agent_specializations))
    # Log2 of N rounded up, but limited by distinct groups
    max_index = max(0, (num_agents - 1).bit_length())
    return min(distinct, max_index)

def compute_game_level_specialization(
    agent_actions: List[Any],
) -> int:
    """
    Placeholder for computing a game‑level specialization metric from
    agent actions. In a full implementation this would analyse the
    distribution of memory actions across agents.
    """
    # Simple proxy: count unique actions
    return len(set(agent_actions))

def validate_specialization_index(index: int, num_agents: int) -> bool:
    """Validate that the specialization index lies within the allowed range."""
    if num_agents <= 0:
        raise ValueError("num_agents must be positive")
    max_index = max(0, (num_agents - 1).bit_length())
    return 0 <= index <= max_index
