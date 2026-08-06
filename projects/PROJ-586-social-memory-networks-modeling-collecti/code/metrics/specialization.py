"""Specialization index computation for multi-agent memory networks.

Calculates distribution-based metrics of per-agent fact contribution,
bounded within a non-negative range [0, 1].

Includes validation logic to log failures if bounds are violated.
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class SpecializationMetrics:
    """Container for specialization computation results."""
    gini_coefficient: float
    shannon_entropy: float
    specialization_index: float
    is_valid: bool
    validation_messages: List[str] = field(default_factory=list)

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

    values = np.array(values, dtype=float)
    if np.all(values == 0):
        return 0.0

    # Sort values
    sorted_values = np.sort(values)
    n = len(sorted_values)

    # Compute cumulative sum
    cumsum = np.cumsum(sorted_values)

    # Gini formula: (2 * sum(i * x_i) - (n + 1) * sum(x_i)) / (n * sum(x_i))
    numerator = 2.0 * np.sum((np.arange(1, n + 1) * sorted_values))
    denominator = n * np.sum(sorted_values)

    if denominator == 0:
        return 0.0

    gini = (numerator - (n + 1) * np.sum(sorted_values)) / denominator

    # Clamp to [0, 1]
    return float(np.clip(gini, 0.0, 1.0))

def compute_shannon_entropy(values: List[float]) -> float:
    """Compute Shannon entropy for a distribution of values.

    Args:
        values: List of non-negative values representing a distribution.

    Returns:
        Shannon entropy (normalized to [0, 1] relative to max entropy).
    """
    if not values or len(values) == 0:
        return 0.0

    values = np.array(values, dtype=float)
    total = np.sum(values)

    if total == 0:
        return 0.0

    # Convert to probabilities
    probs = values / total

    # Filter out zero probabilities to avoid log(0)
    probs = probs[probs > 0]

    # Compute entropy
    entropy = -np.sum(probs * np.log(probs))

    # Normalize by max entropy (log(n))
    n = len(probs)
    if n <= 1:
        return 0.0

    max_entropy = math.log(n)
    normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0.0

    # Clamp to [0, 1]
    return float(np.clip(normalized_entropy, 0.0, 1.0))

def compute_specialization_index(
    agent_facts: Optional[Union[List[Dict[str, Any]], List[List[Any]], Dict[int, List[Any]]]] = None,
    num_agents: Optional[int] = None,
    agents: Optional[Union[List[Dict[str, Any]], List[List[Any]], Dict[int, List[Any]]]] = None
) -> Tuple[float, SpecializationMetrics]:
    """Compute specialization index based on fact distribution across agents.

    The specialization index measures how unevenly facts/contributions are
    distributed among agents. A value of 0 indicates perfect equality
    (all agents contribute equally), while 1 indicates perfect specialization
    (one agent contributes everything).

    Args:
        agent_facts: List of agent fact records. Can be:
            - List of dicts with 'agent_id' and 'facts' keys
            - List of lists where each inner list is facts for one agent
            - Dict mapping agent_id to list of facts
            - If None and agents is provided, uses agents
        num_agents: Total number of agents. If None, inferred from data.
        agents: Alias for agent_facts for compatibility with various call sites.

    Returns:
        Tuple of (specialization_index, SpecializationMetrics).
        specialization_index is in range [0, 1].
    """
    validation_messages = []

    # Handle various input formats
    if agents is not None and agent_facts is None:
        agent_facts = agents

    if agent_facts is None:
        validation_messages.append("No agent data provided; returning 0.0 specialization")
        return 0.0, SpecializationMetrics(
            gini_coefficient=0.0,
            shannon_entropy=0.0,
            specialization_index=0.0,
            is_valid=True,
            validation_messages=validation_messages
        )

    # Extract fact counts per agent
    fact_counts = []

    if isinstance(agent_facts, dict):
        # Dict mapping agent_id to list of facts
        fact_counts = [len(facts) for facts in agent_facts.values()]
        if num_agents is None:
            num_agents = len(agent_facts)
    elif isinstance(agent_facts, list):
        if len(agent_facts) == 0:
            validation_messages.append("Empty agent list; returning 0.0 specialization")
            return 0.0, SpecializationMetrics(
                gini_coefficient=0.0,
                shannon_entropy=0.0,
                specialization_index=0.0,
                is_valid=True,
                validation_messages=validation_messages
            )

        # Check if list of dicts
        if isinstance(agent_facts[0], dict):
            # Extract fact counts from 'facts' or 'contributions' key
            for record in agent_facts:
                facts = record.get('facts', record.get('contributions', []))
                if isinstance(facts, list):
                    fact_counts.append(len(facts))
                else:
                    fact_counts.append(1)
        else:
            # List of lists - each inner list is facts for one agent
            fact_counts = [len(facts) if isinstance(facts, list) else 1 for facts in agent_facts]

        if num_agents is None:
            num_agents = len(fact_counts)
    else:
        validation_messages.append(f"Unexpected agent_facts type: {type(agent_facts)}")
        return 0.0, SpecializationMetrics(
            gini_coefficient=0.0,
            shannon_entropy=0.0,
            specialization_index=0.0,
            is_valid=False,
            validation_messages=validation_messages
        )

    # Ensure we have counts for all agents
    if num_agents is not None and len(fact_counts) < num_agents:
        # Pad with zeros for agents with no facts
        fact_counts.extend([0] * (num_agents - len(fact_counts)))
    elif num_agents is None:
        num_agents = len(fact_counts)

    # Validate inputs
    if num_agents <= 0:
        validation_messages.append(f"Invalid num_agents: {num_agents}")
        return 0.0, SpecializationMetrics(
            gini_coefficient=0.0,
            shannon_entropy=0.0,
            specialization_index=0.0,
            is_valid=False,
            validation_messages=validation_messages
        )

    if len(fact_counts) == 0:
        validation_messages.append("No fact counts extracted")
        return 0.0, SpecializationMetrics(
            gini_coefficient=0.0,
            shannon_entropy=0.0,
            specialization_index=0.0,
            is_valid=True,
            validation_messages=validation_messages
        )

    # Compute metrics
    gini = compute_gini_coefficient(fact_counts)
    entropy = compute_shannon_entropy(fact_counts)

    # Specialization index: high Gini + low entropy = high specialization
    # Normalize: specialization = Gini * (1 - normalized_entropy)
    specialization_index = gini * (1.0 - entropy)

    # Ensure non-negative and bounded
    if specialization_index < 0:
        validation_messages.append(f"Negative specialization index detected: {specialization_index}, clamping to 0")
        specialization_index = 0.0
    if specialization_index > 1:
        validation_messages.append(f"Specialization index > 1 detected: {specialization_index}, clamping to 1")
        specialization_index = 1.0

    is_valid = 0.0 <= specialization_index <= 1.0

    if not is_valid:
        logger.warning(f"Specialization index out of bounds: {specialization_index}")

    metrics = SpecializationMetrics(
        gini_coefficient=gini,
        shannon_entropy=entropy,
        specialization_index=specialization_index,
        is_valid=is_valid,
        validation_messages=validation_messages
    )

    return specialization_index, metrics

def validate_specialization_index(index: float) -> Tuple[bool, str]:
    """Validate that specialization index is within expected bounds.

    Args:
        index: Specialization index value to validate.

    Returns:
        Tuple of (is_valid, message).
    """
    if index < 0:
        return False, f"Specialization index {index} is negative"
    if index > 1:
        return False, f"Specialization index {index} exceeds maximum of 1.0"
    return True, f"Specialization index {index} is within valid range [0, 1]"

def batch_compute_specialization(
    game_results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Compute specialization metrics for multiple game results.

    Args:
        game_results: List of game result dicts, each containing
            'agent_facts' or similar structure.

    Returns:
        Dict with aggregated statistics.
    """
    indices = []
    metrics_list = []

    for result in game_results:
        agent_facts = result.get('agent_facts', result.get('agents', []))
        num_agents = result.get('num_agents', len(agent_facts) if isinstance(agent_facts, list) else None)

        index, metrics = compute_specialization_index(agent_facts, num_agents)
        indices.append(index)
        metrics_list.append(metrics)

    if not indices:
        return {
            'mean': 0.0,
            'std': 0.0,
            'min': 0.0,
            'max': 0.0,
            'count': 0,
            'valid_count': 0
        }

    valid_indices = [i for i in indices if 0.0 <= i <= 1.0]
    valid_metrics = [m for m in metrics_list if m.is_valid]

    return {
        'mean': float(np.mean(indices)),
        'std': float(np.std(indices)),
        'min': float(np.min(indices)),
        'max': float(np.max(indices)),
        'count': len(indices),
        'valid_count': len(valid_indices),
        'valid_percentage': len(valid_indices) / len(indices) * 100 if indices else 0.0
    }

# Legacy alias for backward compatibility
def compute_specialization_index_v1(
    agent_skills: List[Dict[str, Any]],
    num_agents: Optional[int] = None
) -> Tuple[float, SpecializationMetrics]:
    """Legacy alias for compute_specialization_index (v1 compatibility)."""
    return compute_specialization_index(agent_skills, num_agents)
