"""Specialization metrics for multi-agent social memory networks.

Implements the specialization index (Herfindahl-Hirschman Index variant)
to measure how knowledge is distributed across agents in a collective
remembering task.
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, List, Tuple, Optional


@dataclass
class SpecializationMetrics:
    """Metrics describing specialization in a multi-agent system.

    Attributes:
        herfindahl_index: HHI of knowledge distribution (0.0 to 1.0)
        effective_agents: Number of agents that would produce same HHI if equal
        specialization_ratio: Ratio of max share to average share
        entropy: Shannon entropy of distribution (normalized)
    """
    herfindahl_index: float
    effective_agents: float
    specialization_ratio: float
    entropy: float
    agent_shares: List[float] = field(default_factory=list)


def validate_specialization_index(index: float) -> bool:
    """Validate that specialization index is in valid range [0, 1].

    Args:
        index: Computed specialization index value

    Returns:
        True if valid, False otherwise
    """
    return 0.0 <= index <= 1.0


def compute_game_level_specialization(
    agent_knowledge_counts: List[int],
    num_agents: Optional[int] = None
) -> Tuple[SpecializationMetrics, float]:
    """Compute specialization metrics for a single game.

    Args:
        agent_knowledge_counts: List of knowledge items held by each agent
        num_agents: Total number of agents (optional, defaults to len(counts))

    Returns:
        Tuple of (SpecializationMetrics, specialization_index)
    """
    if not agent_knowledge_counts:
        zero_metrics = SpecializationMetrics(
            herfindahl_index=0.0,
            effective_agents=0.0,
            specialization_ratio=0.0,
            entropy=0.0,
            agent_shares=[]
        )
        return zero_metrics, 0.0

    total_knowledge = sum(agent_knowledge_counts)
    if total_knowledge == 0:
        zero_metrics = SpecializationMetrics(
            herfindahl_index=0.0,
            effective_agents=float(len(agent_knowledge_counts)) if agent_knowledge_counts else 0.0,
            specialization_ratio=0.0,
            entropy=0.0,
            agent_shares=[0.0] * len(agent_knowledge_counts)
        )
        return zero_metrics, 0.0

    # Calculate shares (proportion of total knowledge per agent)
    shares = [count / total_knowledge for count in agent_knowledge_counts]

    # Herfindahl-Hirschman Index: sum of squared shares
    hhi = sum(s ** 2 for s in shares)

    # Effective number of agents: 1 / HHI
    effective_agents = 1.0 / hhi if hhi > 0 else float(len(agent_knowledge_counts))

    # Specialization ratio: max share / average share
    avg_share = 1.0 / len(agent_knowledge_counts) if agent_knowledge_counts else 0.0
    max_share = max(shares) if shares else 0.0
    specialization_ratio = max_share / avg_share if avg_share > 0 else 0.0

    # Normalized Shannon entropy
    entropy = 0.0
    for s in shares:
        if s > 0:
            entropy -= s * math.log(s)
    max_entropy = math.log(len(agent_knowledge_counts)) if len(agent_knowledge_counts) > 1 else 1.0
    normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0.0

    metrics = SpecializationMetrics(
        herfindahl_index=hhi,
        effective_agents=effective_agents,
        specialization_ratio=specialization_ratio,
        entropy=normalized_entropy,
        agent_shares=shares
    )

    return metrics, hhi


def compute_specialization_index(
    agent_list: Optional[List[Any]] = None,
    num_agents: Optional[int] = None,
    agents: Optional[List[Any]] = None,
    agent_count: Optional[int] = None,
    game_id: Optional[int] = None
) -> Tuple[float, SpecializationMetrics]:
    """Compute specialization index from various input shapes.

    This function is designed to be tolerant of different calling conventions:
    1. compute_specialization_index(agent_list) - list of agent skills/knowledge
    2. compute_specialization_index(agent_list, num_agents=N) - with explicit count
    3. compute_specialization_index(agents=..., num_agents=...) - keyword style
    4. compute_specialization_index(agent_count, game_id) - legacy (uses agent_count as list length)

    Args:
        agent_list: List of agent knowledge/skills (positional or via 'agents')
        num_agents: Explicit agent count (optional)
        agents: Alternative keyword for agent_list
        agent_count: Legacy positional argument (interpreted as list length if game_id provided)
        game_id: Legacy positional argument

    Returns:
        Tuple of (specialization_index, SpecializationMetrics)
    """
    # Handle legacy: compute_specialization_index(agent_count, game_id)
    if agent_count is not None and game_id is not None:
        # Treat agent_count as the length of a synthetic list
        knowledge_counts = [1] * agent_count
        return compute_game_level_specialization(knowledge_counts, agent_count)

    # Resolve agent_list from positional or keyword
    if agent_list is None:
        agent_list = agents

    # If we have an actual list of agents with knowledge
    if agent_list is not None:
        if isinstance(agent_list, list):
            # Extract knowledge counts if agents have a 'knowledge_count' attribute
            if len(agent_list) > 0 and hasattr(agent_list[0], 'knowledge_count'):
                knowledge_counts = [a.knowledge_count for a in agent_list]
            else:
                # Assume list elements are knowledge counts or derive from length
                knowledge_counts = [1] * len(agent_list)

            n_agents = num_agents if num_agents is not None else len(agent_list)
            return compute_game_level_specialization(knowledge_counts, n_agents)

    # Fallback: if no data provided, return neutral metrics
    n = num_agents if num_agents is not None else (agent_count if agent_count is not None else 0)
    if n > 0:
        knowledge_counts = [1] * n
        return compute_game_level_specialization(knowledge_counts, n)

    # Empty case
    zero_metrics = SpecializationMetrics(
        herfindahl_index=0.0,
        effective_agents=0.0,
        specialization_ratio=0.0,
        entropy=0.0,
        agent_shares=[]
    )
    return 0.0, zero_metrics