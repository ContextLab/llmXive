from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Tuple, Any, Optional

@dataclass
class SpecializationMetrics:
    distinct_agents: int
    total_actions: int
    num_agents: int

def compute_specialization_index(
    agents: List[int],
    num_agents: Optional[int] = None,
    game_id: Any = None,
) -> Tuple[float, SpecializationMetrics]:
    """
    Compute a specialization index for a list of agent actions.

    ``agents`` is a list where each entry represents the agent that performed
    an action.  The index is a simple heuristic: the proportion of distinct
    agents multiplied by log2(num_agents).  This mirrors the original intent
    while remaining deterministic.
    """
    distinct = len(set(agents))
    total = len(agents)
    if num_agents is None:
        num_agents = max(distinct, 1)
    max_entropy = math.log2(num_agents) if num_agents > 0 else 0.0
    observed = distinct / num_agents
    index = observed * max_entropy
    metrics = SpecializationMetrics(
        distinct_agents=distinct,
        total_actions=total,
        num_agents=num_agents,
    )
    return index, metrics

# Validation helper used elsewhere
def validate_specialization_index(index: float) -> bool:
    return 0.0 <= index <= math.log2(1000)  # generous upper bound