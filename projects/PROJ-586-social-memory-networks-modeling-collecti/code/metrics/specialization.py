"""Specialization metrics for multi-agent social memory networks.

Implements the specialization index as a distribution-based metric of
per-agent fact contribution, bounded between 0 and log2(N_agents).
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
    specialization_index: float = 0.0
    entropy: float = 0.0
    gini_coefficient: float = 0.0
    max_possible_index: float = 0.0
    normalized_index: float = 0.0
    per_agent_contributions: List[float] = field(default_factory=list)


def compute_gini_coefficient(values: List[Union[int, float]]) -> float:
    """Compute the Gini coefficient for a list of values.

    The Gini coefficient measures inequality in a distribution.
    0 = perfect equality, 1 = perfect inequality.

    Args:
        values: List of non-negative numeric values.

    Returns:
        Gini coefficient between 0 and 1.
    """
    if not values or len(values) == 0:
        return 0.0

    n = len(values)
    sorted_values = sorted(values)
    cumulative = np.cumsum(sorted_values)

    if cumulative[-1] == 0:
        return 0.0

    gini = (2 * np.sum((np.arange(1, n + 1) * sorted_values))) / (n * cumulative[-1]) - (n + 1) / n
    return max(0.0, min(1.0, gini))


def compute_shannon_entropy(proportions: List[float]) -> float:
    """Compute Shannon entropy for a probability distribution.

    Args:
        proportions: List of non-negative values that sum to 1 (or will be normalized).

    Returns:
        Shannon entropy in bits (log base 2).
    """
    if not proportions or len(proportions) == 0:
        return 0.0

    total = sum(proportions)
    if total == 0:
        return 0.0

    normalized = [p / total for p in proportions]
    entropy = 0.0
    for p in normalized:
        if p > 0:
            entropy -= p * math.log2(p)

    return entropy


def compute_specialization_index(
    agent_facts: Union[List[Any], Dict[str, Any], List[Dict[str, Any]], None],
    num_agents: Optional[int] = None
) -> Tuple[float, SpecializationMetrics]:
    """Compute the specialization index for a multi-agent system.

    The specialization index measures how evenly facts are distributed across agents.
    It is bounded between 0 (perfect specialization, one agent knows everything)
    and log2(N_agents) (perfect equal distribution).

    FR-004: Calculate distribution-based metric of per-agent fact contribution,
    bounded 0 to log2(N_agents).

    Args:
        agent_facts: Can be:
            - A list of fact counts per agent: [count1, count2, ...]
            - A dict mapping agent_id to fact list: {agent_id: [facts]}
            - A list of dicts with agent info: [{'agent_id': ..., 'facts': [...]}]
            - A list of game results with facts_per_agent attribute
            - None or empty list (returns 0)
        num_agents: Optional override for number of agents. If None, inferred from data.

    Returns:
        Tuple of (specialization_index, SpecializationMetrics object).
        The index is normalized to [0, log2(N_agents)].
    """
    # Handle empty/None input
    if agent_facts is None:
        return 0.0, SpecializationMetrics()

    # Extract per-agent fact counts
    fact_counts = []
    actual_num_agents = 0

    if isinstance(agent_facts, list):
        if len(agent_facts) == 0:
            return 0.0, SpecializationMetrics()

        # Check if it's a list of counts
        if all(isinstance(x, (int, float)) for x in agent_facts):
            fact_counts = [int(x) for x in agent_facts]
            actual_num_agents = len(fact_counts)
        # Check if it's a list of dicts with facts
        elif all(isinstance(x, dict) and 'facts' in x for x in agent_facts):
            fact_counts = [len(item['facts']) for item in agent_facts]
            actual_num_agents = len(fact_counts)
        # Check if it's a list of dicts with agent_id
        elif all(isinstance(x, dict) and 'agent_id' in x for x in agent_facts):
            # Count facts per agent_id
            agent_fact_counts: Dict[str, int] = {}
            for item in agent_facts:
                agent_id = item['agent_id']
                facts = item.get('facts', [])
                agent_fact_counts[agent_id] = len(facts)
            fact_counts = list(agent_fact_counts.values())
            actual_num_agents = len(fact_counts)
        # Check if it's a list of game result-like objects
        elif len(agent_facts) > 0 and hasattr(agent_facts[0], 'facts_per_agent'):
            # Extract facts_per_agent from first result if it's a list
            first_result = agent_facts[0]
            if isinstance(first_result.facts_per_agent, (list, dict)):
                if isinstance(first_result.facts_per_agent, list):
                    fact_counts = first_result.facts_per_agent
                    actual_num_agents = len(fact_counts)
                elif isinstance(first_result.facts_per_agent, dict):
                    fact_counts = list(first_result.facts_per_agent.values())
                    actual_num_agents = len(fact_counts)
            else:
                # Single value or unexpected format
                fact_counts = [0]
                actual_num_agents = 1
        else:
            # Fallback: try to get length of each item
            fact_counts = [len(x) if hasattr(x, '__len__') else 0 for x in agent_facts]
            actual_num_agents = len(fact_counts)

    elif isinstance(agent_facts, dict):
        # Dict mapping agent_id to facts list
        fact_counts = [len(v) for v in agent_facts.values()]
        actual_num_agents = len(fact_counts)

    else:
        # Unknown type, try to get length
        try:
            fact_counts = [len(agent_facts)]
            actual_num_agents = 1
        except (TypeError, AttributeError):
            return 0.0, SpecializationMetrics()

    # Use provided num_agents or infer from data
    if num_agents is not None:
        actual_num_agents = num_agents

    if actual_num_agents <= 0 or len(fact_counts) == 0:
        return 0.0, SpecializationMetrics()

    # Normalize fact_counts to proportions
    total_facts = sum(fact_counts)
    if total_facts == 0:
        # No facts distributed, perfect equality (all 0)
        # This is a degenerate case; return 0 as specialization
        return 0.0, SpecializationMetrics(
            specialization_index=0.0,
            entropy=0.0,
            gini_coefficient=0.0,
            max_possible_index=math.log2(actual_num_agents) if actual_num_agents > 1 else 0.0,
            normalized_index=0.0,
            per_agent_contributions=[0.0] * actual_num_agents
        )

    proportions = [c / total_facts for c in fact_counts]

    # Compute Shannon entropy (in bits)
    entropy = compute_shannon_entropy(proportions)

    # Maximum possible entropy is log2(N_agents)
    max_entropy = math.log2(actual_num_agents) if actual_num_agents > 1 else 0.0

    # Specialization index: we use normalized entropy
    # Higher entropy = more equal distribution = less specialization
    # We want: 0 = perfect specialization (one agent knows all),
    #          max = perfect equal distribution
    # So we use entropy directly as the index, bounded by log2(N)
    if max_entropy > 0:
        specialization_index = entropy
    else:
        specialization_index = 0.0

    # Compute Gini coefficient as additional metric
    gini = compute_gini_coefficient(fact_counts)

    # Normalize index to [0, 1] range for comparison
    normalized_index = entropy / max_entropy if max_entropy > 0 else 0.0

    metrics = SpecializationMetrics(
        specialization_index=specialization_index,
        entropy=entropy,
        gini_coefficient=gini,
        max_possible_index=max_entropy,
        normalized_index=normalized_index,
        per_agent_contributions=proportions
    )

    return specialization_index, metrics


def validate_specialization_index(
    index: float,
    num_agents: int,
    tolerance: float = 1e-6
) -> bool:
    """Validate that a specialization index is within expected bounds.

    FR-004 requirement: index must be bounded between 0 and log2(N_agents).

    Args:
        index: The computed specialization index.
        num_agents: Number of agents in the system.
        tolerance: Allowed numerical tolerance for bounds checking.

    Returns:
        True if index is within valid bounds, False otherwise.
    """
    if num_agents <= 0:
        return False

    max_index = math.log2(num_agents) if num_agents > 1 else 0.0
    min_index = 0.0

    return (min_index - tolerance) <= index <= (max_index + tolerance)


def batch_compute_specialization(
    game_results: List[Any],
    num_agents: Optional[int] = None
) -> Dict[str, Any]:
    """Compute specialization metrics for a batch of game results.

    Args:
        game_results: List of game result objects or dicts.
        num_agents: Optional override for number of agents.

    Returns:
        Dictionary with aggregated specialization statistics.
    """
    if not game_results:
        return {
            'mean_index': 0.0,
            'std_index': 0.0,
            'min_index': 0.0,
            'max_index': 0.0,
            'count': 0
        }

    indices = []
    metrics_list = []

    for result in game_results:
        # Extract facts_per_agent from result
        if hasattr(result, 'facts_per_agent'):
            facts = result.facts_per_agent
        elif isinstance(result, dict) and 'facts_per_agent' in result:
            facts = result['facts_per_agent']
        else:
            continue

        idx, metrics = compute_specialization_index(facts, num_agents)
        indices.append(idx)
        metrics_list.append(metrics)

    if not indices:
        return {
            'mean_index': 0.0,
            'std_index': 0.0,
            'min_index': 0.0,
            'max_index': 0.0,
            'count': 0
        }

    return {
        'mean_index': float(np.mean(indices)),
        'std_index': float(np.std(indices)),
        'min_index': float(np.min(indices)),
        'max_index': float(np.max(indices)),
        'count': len(indices),
        'all_indices': indices,
        'all_metrics': metrics_list
    }