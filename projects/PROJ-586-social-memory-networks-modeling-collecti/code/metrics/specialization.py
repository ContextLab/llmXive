"""Specialization index computation for multi-agent memory networks.

Calculates distribution-based metrics of per-agent fact contribution,
bounded 0 to log2(N_agents).
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

@dataclass
class SpecializationMetrics:
    """Container for specialization-related metrics."""
    specialization_index: float
    gini_coefficient: float
    shannon_entropy: float
    max_entropy: float
    normalized_entropy: float
    agent_contributions: Dict[int, int] = field(default_factory=dict)

def compute_gini_coefficient(values: List[float]) -> float:
    """Compute Gini coefficient for a list of values.

    The Gini coefficient measures inequality in a distribution.
    0 = perfect equality, 1 = perfect inequality.

    Args:
        values: List of non-negative numeric values.

    Returns:
        Gini coefficient in range [0, 1].
    """
    if not values or len(values) == 0:
        return 0.0

    values = [v if v >= 0 else 0 for v in values]
    n = len(values)
    if n == 1:
        return 0.0

    sorted_values = sorted(values)
    cumsum = np.cumsum(sorted_values)
    total = cumsum[-1]

    if total == 0:
        return 0.0

    gini = (2 * np.sum((np.arange(1, n + 1) * sorted_values))) / (n * total) - (n + 1) / n
    return max(0.0, min(1.0, gini))

def compute_shannon_entropy(values: List[float]) -> Tuple[float, float]:
    """Compute Shannon entropy and maximum possible entropy.

    Args:
        values: List of non-negative numeric values representing counts.

    Returns:
        Tuple of (shannon_entropy, max_entropy).
    """
    if not values or len(values) == 0:
        return 0.0, 0.0

    total = sum(values)
    if total == 0:
        return 0.0, 0.0

    probabilities = [v / total for v in values if v > 0]
    if len(probabilities) == 0:
        return 0.0, 0.0

    entropy = -sum(p * math.log2(p) for p in probabilities if p > 0)
    max_entropy = math.log2(len(probabilities)) if len(probabilities) > 1 else 0.0

    return entropy, max(entropy, 0.0)

def compute_specialization_index(
    agent_facts: Union[List, Dict, None],
    num_agents: Optional[int] = None,
    agents: Optional[Any] = None
) -> Tuple[float, SpecializationMetrics]:
    """Compute the specialization index for agent contributions.

    The specialization index measures how specialized the distribution of
    facts across agents is. It is bounded between 0 (perfect specialization,
    one agent knows everything) and log2(N_agents) (perfectly uniform).

    Args:
        agent_facts: Either a list of fact counts per agent, a dict mapping
            agent_id to fact count, or None/empty for default behavior.
        num_agents: Optional explicit number of agents. If None, inferred from
            agent_facts.
        agents: Alternative parameter for backward compatibility; treated as
            agent_facts if provided.

    Returns:
        Tuple of (specialization_index, metrics_dict).
    """
    # Handle various input shapes for backward compatibility
    if agents is not None and agent_facts is None:
        agent_facts = agents

    # Normalize input to a list of counts
    if agent_facts is None or (isinstance(agent_facts, list) and len(agent_facts) == 0):
        # Default: uniform distribution across 1 agent
        if num_agents is None or num_agents <= 0:
            num_agents = 1
        counts = [1] * num_agents
    elif isinstance(agent_facts, dict):
        if not agent_facts:
            if num_agents is None or num_agents <= 0:
                num_agents = 1
            counts = [0] * num_agents
        else:
            num_agents = num_agents if num_agents is not None else len(agent_facts)
            counts = [agent_facts.get(i, 0) for i in range(num_agents)]
    elif isinstance(agent_facts, (list, tuple)):
        if len(agent_facts) == 0:
            if num_agents is None or num_agents <= 0:
                num_agents = 1
            counts = [1] * num_agents
        else:
            counts = list(agent_facts)
            if num_agents is None:
                num_agents = len(counts)
    else:
        # Single value or unexpected type
        if num_agents is None or num_agents <= 0:
            num_agents = 1
        counts = [1] * num_agents

    # Ensure non-negative
    counts = [max(0, c) for c in counts]
    total = sum(counts)

    if total == 0:
        # No facts distributed
        if num_agents <= 1:
            spec_index = 0.0
        else:
            spec_index = 0.0  # Uniform but empty
        metrics = SpecializationMetrics(
            specialization_index=spec_index,
            gini_coefficient=0.0,
            shannon_entropy=0.0,
            max_entropy=math.log2(num_agents) if num_agents > 1 else 0.0,
            normalized_entropy=0.0,
            agent_contributions={i: c for i, c in enumerate(counts)}
        )
        return spec_index, metrics

    # Compute Gini coefficient
    gini = compute_gini_coefficient(counts)

    # Compute Shannon entropy
    entropy, max_entropy = compute_shannon_entropy(counts)

    # Normalize entropy to [0, 1]
    normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0.0

    # Specialization index: based on entropy
    # Lower entropy = higher specialization (one agent knows most)
    # Higher entropy = lower specialization (distributed knowledge)
    # We define specialization_index as: max_entropy - entropy
    # This gives: 0 (perfectly uniform) to max_entropy (one agent knows all)
    if num_agents <= 1:
        spec_index = 0.0
    else:
        spec_index = max_entropy - entropy
        # Ensure bounds [0, log2(N)]
        spec_index = max(0.0, min(spec_index, math.log2(num_agents)))

    metrics = SpecializationMetrics(
        specialization_index=round(spec_index, 6),
        gini_coefficient=round(gini, 6),
        shannon_entropy=round(entropy, 6),
        max_entropy=round(max_entropy, 6),
        normalized_entropy=round(normalized_entropy, 6),
        agent_contributions={i: c for i, c in enumerate(counts)}
    )

    return round(spec_index, 6), metrics

def validate_specialization_index(index: float, num_agents: int) -> Tuple[bool, str]:
    """Validate that specialization index is within expected bounds.

    Args:
        index: Computed specialization index.
        num_agents: Number of agents in the system.

    Returns:
        Tuple of (is_valid, message).
    """
    if num_agents <= 0:
        return False, "num_agents must be positive"

    if index < 0:
        return False, f"Specialization index {index} is negative"

    max_val = math.log2(num_agents)
    if index > max_val + 1e-9:  # Small tolerance for floating point
        return False, f"Specialization index {index} exceeds max {max_val}"

    return True, "Valid"

def batch_compute_specialization(
    game_results: List[Dict[str, Any]]
) -> List[Tuple[float, SpecializationMetrics]]:
    """Compute specialization index for multiple game results.

    Args:
        game_results: List of dicts with 'facts_per_agent' key.

    Returns:
        List of (specialization_index, metrics) tuples.
    """
    results = []
    for game in game_results:
        facts = game.get('facts_per_agent', [])
        num_agents = game.get('num_agents', len(facts) if facts else 1)
        idx, metrics = compute_specialization_index(facts, num_agents=num_agents)
        results.append((idx, metrics))
    return results

# Backward compatibility aliases
def compute_specialization_index_v1(
    agent_skills: Union[List, Dict, None],
    num_agents: Optional[int] = None,
    agents: Optional[Any] = None
) -> Tuple[float, SpecializationMetrics]:
    """Alias for compute_specialization_index with legacy signature."""
    return compute_specialization_index(agent_skills, num_agents, agents)