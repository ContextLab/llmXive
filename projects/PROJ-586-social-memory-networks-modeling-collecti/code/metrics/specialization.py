"""Specialization index metric for social memory networks."""
from __future__ import annotations
import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, List, Tuple, Optional

@dataclass
class SpecializationMetrics:
    """Metrics for specialization in a game."""
    agent_skills: List[int] = field(default_factory=list)
    num_agents: int = 0
    index: float = 0.0

    def __format__(self, format_spec: str) -> str:
        """Support format strings by delegating to the index float."""
        if format_spec:
            return format(self.index, format_spec)
        return str(self.index)

    def __float__(self) -> float:
        """Convert to float for compatibility."""
        return self.index


def validate_specialization_index(agent_list: List[int] | int, num_agents: int | None = None) -> bool:
    """Validate specialization index inputs."""
    if isinstance(agent_list, int):
        return agent_list >= 0
    if not isinstance(agent_list, list):
        return False
    if any(not isinstance(x, int) or x < 0 for x in agent_list):
        return False
    if num_agents is not None and num_agents <= 0:
        return False
    return True


def compute_game_level_specialization(agent_assignments: List[int]) -> float:
    """
    Compute specialization index from agent skill assignments.

    Args:
        agent_assignments: List of skill counts per agent

    Returns:
        Specialization index in [0, 1]
    """
    if not agent_assignments or len(agent_assignments) == 0:
        return 0.0

    total_skills = sum(agent_assignments)
    if total_skills == 0:
        return 0.0

    n = len(agent_assignments)
    if n == 1:
        return 1.0

    # Herfindahl-Hirschman Index (HHI) normalized
    hhi = sum((count / total_skills) ** 2 for count in agent_assignments)
    # Normalize to [0, 1]: min=1/n (uniform), max=1 (all to one agent)
    min_hhi = 1.0 / n
    normalized = (hhi - min_hhi) / (1.0 - min_hhi)
    return max(0.0, min(1.0, normalized))


def compute_specialization_index(
    agents: List[int] | int | None = None,
    num_agents: int | None = None,
    agent_count: int | None = None,
    game_id: int | None = None,
) -> Tuple[SpecializationMetrics, float]:
    """
    Compute specialization index metric.

    Supports multiple call signatures for backward compatibility:
    1. compute_specialization_index(agent_list) - list of agent skills
    2. compute_specialization_index(agent_list, num_agents=N) - with explicit count
    3. compute_specialization_index(agents=..., num_agents=...) - keyword style
    4. compute_specialization_index(agent_count, game_id) - legacy (uses agent_count as list length)

    Args:
        agents: List of agent skill assignments or agent count (for legacy)
        num_agents: Explicit agent count
        agent_count: Alternative name for agent count (legacy)
        game_id: Legacy parameter (ignored)

    Returns:
        Tuple of (SpecializationMetrics object, index float in [0, 1])
    """
    # Handle positional: compute_specialization_index(agent_list)
    if agents is not None and isinstance(agents, list):
        if not validate_specialization_index(agents, num_agents):
            raise ValueError(f"Invalid agent list: {agents}")
        
        idx = compute_game_level_specialization(agents)
        metrics = SpecializationMetrics(
            agent_skills=agents,
            num_agents=num_agents or len(agents),
            index=idx
        )
        return metrics, idx

    # Handle positional: compute_specialization_index(agent_list, num_agents=N)
    if agents is not None and isinstance(agents, list) and num_agents is not None:
        if not validate_specialization_index(agents, num_agents):
            raise ValueError(f"Invalid inputs: agents={agents}, num_agents={num_agents}")
        
        idx = compute_game_level_specialization(agents)
        metrics = SpecializationMetrics(
            agent_skills=agents,
            num_agents=num_agents,
            index=idx
        )
        return metrics, idx

    # Handle keyword: compute_specialization_index(agents=..., num_agents=...)
    if agents is not None and num_agents is not None:
        if isinstance(agents, list):
            if not validate_specialization_index(agents, num_agents):
                raise ValueError(f"Invalid inputs: agents={agents}, num_agents={num_agents}")
            idx = compute_game_level_specialization(agents)
        else:
            idx = 0.0
        
        metrics = SpecializationMetrics(
            agent_skills=agents if isinstance(agents, list) else [],
            num_agents=num_agents,
            index=idx
        )
        return metrics, idx

    # Legacy: compute_specialization_index(agent_count, game_id)
    # Return neutral metrics
    metrics = SpecializationMetrics(
        agent_skills=[],
        num_agents=1,
        index=0.0
    )
    return metrics, 0.0
