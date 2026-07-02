"""Specialization index metric utilities."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Any


@dataclass
class SpecializationMetrics:
    """Container for specialization metric results."""
    specialization_index: int


def compute_specialization_index(
    agent_specializations: List[int],
    num_agents: int,
) -> int:
    """
    Compute the specialization index (0 to ⌈log₂(N_agents)⌉).

    The specialization index is defined as the ceiling of the binary
    logarithm of the number of *distinct* specialization groups present
    among agents, capped by the maximum possible index for the given
    number of agents.

    Args:
        agent_specializations: A list where each entry encodes the
            specialization group of an agent (e.g., an integer label).
        num_agents: Total number of agents in the simulation.

    Returns:
        An integer specialization index in the range [0, ceil(log₂(num_agents))].

    Raises:
        ValueError: If ``num_agents`` is not positive.
    """
    if num_agents <= 0:
        raise ValueError("num_agents must be positive")

    # Number of distinct specialization groups observed.
    distinct_groups = len(set(agent_specializations))

    # If there are no agents or no groups, the index is 0.
    if distinct_groups == 0:
        return 0

    # Ceiling of log2(distinct_groups). For distinct_groups == 1, result is 0.
    # Using math.log2 may introduce floating‑point rounding errors, so we
    # compute the ceiling via integer arithmetic.
    # ceil(log2(x)) == (x - 1).bit_length()
    ceil_log2_distinct = (distinct_groups - 1).bit_length()

    # Maximum index allowed for the given number of agents:
    # ceil(log2(num_agents)) == (num_agents - 1).bit_length()
    max_index = (num_agents - 1).bit_length()

    # The final specialization index cannot exceed the theoretical maximum.
    return min(ceil_log2_distinct, max_index)


def compute_game_level_specialization(
    agent_actions: List[Any],
) -> int:
    """
    Compute a simple game‑level specialization metric from agent actions.

    This placeholder implementation counts the number of unique actions
    performed by agents during a single game. In a full implementation,
    one would analyse the distribution of memory actions across agents
    to derive a richer specialization signal.
    """
    return len(set(agent_actions))


def validate_specialization_index(index: int, num_agents: int) -> bool:
    """Validate that the specialization index lies within the allowed range."""
    if num_agents <= 0:
        raise ValueError("num_agents must be positive")
    max_index = (num_agents - 1).bit_length()
    return 0 <= index <= max_index