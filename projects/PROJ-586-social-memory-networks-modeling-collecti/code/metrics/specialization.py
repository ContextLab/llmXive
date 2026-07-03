"""Specialization index metric for social memory networks."""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, List, Tuple, Optional


@dataclass
class SpecializationMetrics:
    """Metrics for specialization index."""
    index: float
    agent_counts: List[int] = field(default_factory=list)
    herfindahl: float = 0.0
    entropy: float = 0.0
    
    def __format__(self, format_spec: str) -> str:
        """Support format strings like {metrics:.6f}."""
        if format_spec:
            return format(self.index, format_spec)
        return str(self.index)
    
    def __float__(self) -> float:
        """Allow float() conversion."""
        return self.index
    
    def __str__(self) -> str:
        """String representation."""
        return f"{self.index:.6f}"


def validate_specialization_index(index: float) -> Tuple[bool, str]:
    """Validate specialization index.
    
    Args:
        index: The specialization index value
        
    Returns:
        (is_valid, error_message)
    """
    if not isinstance(index, (int, float)):
        return False, f"index must be numeric, got {type(index)}"
    if index < 0.0 or index > 1.0:
        return False, f"index must be in [0, 1], got {index}"
    return True, ""


def compute_game_level_specialization(
    agent_list: List[int],
) -> Tuple[float, dict]:
    """Compute specialization for a single game.
    
    Args:
        agent_list: List of agent skill assignments
        
    Returns:
        (specialization_index, metrics_dict)
    """
    if not agent_list:
        return 0.0, {"herfindahl": 0.0, "entropy": 0.0}
    
    # Count occurrences of each agent skill
    counts = Counter(agent_list)
    n = len(agent_list)
    
    # Herfindahl index: sum of squared proportions
    herfindahl = sum((c / n) ** 2 for c in counts.values())
    
    # Entropy: negative sum of p*log(p)
    entropy = -sum((c / n) * math.log(c / n) for c in counts.values() if c > 0)
    
    # Normalize entropy to [0, 1]
    max_entropy = math.log(len(counts)) if len(counts) > 1 else 0
    normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
    
    # Specialization = 1 - normalized_entropy (high entropy = low specialization)
    specialization = 1.0 - normalized_entropy
    
    return specialization, {
        "herfindahl": herfindahl,
        "entropy": entropy,
        "normalized_entropy": normalized_entropy,
    }


def compute_specialization_index(
    agents: List[int] | None = None,
    num_agents: int | None = None,
    agent_list: List[int] | None = None,
    agent_count: int | None = None,
    game_id: int | None = None,
) -> Tuple[float, SpecializationMetrics]:
    """Compute specialization index metric.
    
    Supports multiple call signatures:
    1. compute_specialization_index(agent_list) - list of agent skills
    2. compute_specialization_index(agent_list, num_agents=N) - with explicit count
    3. compute_specialization_index(agents=..., num_agents=...) - keyword style
    4. compute_specialization_index(agent_count, game_id) - legacy (uses agent_count as list length)
    
    Args:
        agents: List of agent skill assignments
        num_agents: Number of agents (for context)
        agent_list: Alias for agents parameter
        agent_count: Legacy parameter (used as list length if agents is None)
        game_id: Legacy parameter (ignored)
        
    Returns:
        (specialization_index as float, SpecializationMetrics object)
    """
    # Resolve which parameter was passed
    actual_agents = agents or agent_list
    
    # Handle legacy positional call: compute_specialization_index(agent_count, game_id)
    if actual_agents is None and agent_count is not None:
        if isinstance(agent_count, int):
            # Legacy: agent_count is the list length, create a dummy list
            actual_agents = [i % max(1, (agent_count // 2)) for i in range(agent_count)]
        elif isinstance(agent_count, list):
            actual_agents = agent_count
    
    # Final validation
    if actual_agents is None:
        actual_agents = []
    
    if not isinstance(actual_agents, list):
        actual_agents = list(actual_agents)
    
    # Compute specialization
    spec_index, metrics_dict = compute_game_level_specialization(actual_agents)
    
    # Validate
    is_valid, error_msg = validate_specialization_index(spec_index)
    if not is_valid:
        raise ValueError(error_msg)
    
    metrics = SpecializationMetrics(
        index=spec_index,
        agent_counts=actual_agents,
        herfindahl=metrics_dict.get("herfindahl", 0.0),
        entropy=metrics_dict.get("entropy", 0.0),
    )
    
    return spec_index, metrics
