"""Specialization index computation for multi-agent memory networks.

This module implements the computation of a distribution-based metric
of per-agent fact contribution (specialization index), bounded within
a non-negative range [0, 1].
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
    specialization_index: float
    gini_coefficient: Optional[float] = None
    shannon_entropy: Optional[float] = None
    max_contribution: Optional[float] = None
    min_contribution: Optional[float] = None
    mean_contribution: Optional[float] = None
    std_contribution: Optional[float] = None
    validation_passed: bool = True
    validation_message: str = ""


def compute_gini_coefficient(values: List[float]) -> float:
    """Compute the Gini coefficient for a list of values.

    The Gini coefficient measures inequality in a distribution.
    0 = perfect equality (all values equal)
    1 = perfect inequality (one value has all)

    Args:
        values: List of non-negative numeric values.

    Returns:
        Gini coefficient in range [0, 1].
    """
    if not values or len(values) == 0:
        return 0.0

    n = len(values)
    sorted_values = sorted(values)
    cumsum = np.cumsum(sorted_values)
    total = cumsum[-1]

    if total == 0:
        return 0.0

    gini = (2.0 * np.sum((np.arange(1, n + 1) * sorted_values))) / (n * total) - (n + 1) / n
    return max(0.0, min(1.0, gini))


def compute_shannon_entropy(values: List[float]) -> float:
    """Compute Shannon entropy for a distribution of values.

    Args:
        values: List of non-negative numeric values representing counts or weights.

    Returns:
        Shannon entropy in nats (natural log base).
    """
    if not values or len(values) == 0:
        return 0.0

    total = sum(values)
    if total == 0:
        return 0.0

    probabilities = [v / total for v in values if v > 0]
    entropy = -sum(p * math.log(p) for p in probabilities if p > 0)
    return entropy


def compute_specialization_index(
    agent_contributions: Union[List[float], Dict[str, float], Any, None],
    num_agents: Optional[int] = None
) -> Tuple[float, SpecializationMetrics]:
    """Compute the specialization index for a set of agent contributions.

    The specialization index measures how unevenly facts/contributions are
    distributed among agents. A value of 0 indicates perfect equality
    (all agents contribute equally), while higher values indicate greater
    specialization (unequal distribution).

    The metric is bounded to [0, 1] where:
    - 0: Perfect equality (no specialization)
    - 1: Maximum inequality (complete specialization)

    Args:
        agent_contributions: Can be:
            - List of floats: contribution values for each agent
            - Dict[str, float]: mapping of agent_id to contribution
            - List of ints: raw counts of contributions
            - Any other iterable: will be converted to list of floats
        num_agents: Optional explicit number of agents. If None, inferred
            from the length of agent_contributions.

    Returns:
        Tuple of (specialization_index, SpecializationMetrics)
    """
    # Handle empty or None input
    if agent_contributions is None:
        logger.warning("compute_specialization_index received None input")
        return 0.0, SpecializationMetrics(
            specialization_index=0.0,
            validation_passed=False,
            validation_message="Input was None"
        )

    # Convert various input types to a list of floats
    contributions_list: List[float] = []

    if isinstance(agent_contributions, dict):
        contributions_list = [float(v) for v in agent_contributions.values()]
    elif isinstance(agent_contributions, (list, tuple)):
        try:
            contributions_list = [float(v) for v in agent_contributions]
        except (TypeError, ValueError) as e:
            logger.warning(f"Could not convert contributions to floats: {e}")
            return 0.0, SpecializationMetrics(
                specialization_index=0.0,
                validation_passed=False,
                validation_message=f"Invalid input type: {e}"
            )
    else:
        # Try to iterate if it's some other iterable
        try:
            contributions_list = [float(v) for v in agent_contributions]
        except (TypeError, ValueError) as e:
            logger.warning(f"Could not iterate over contributions: {e}")
            return 0.0, SpecializationMetrics(
                specialization_index=0.0,
                validation_passed=False,
                validation_message=f"Cannot iterate input: {e}"
            )

    # Handle empty list
    if not contributions_list:
        logger.warning("compute_specialization_index received empty list")
        return 0.0, SpecializationMetrics(
            specialization_index=0.0,
            validation_passed=False,
            validation_message="Input list was empty"
        )

    # Determine number of agents
    if num_agents is not None:
        n_agents = num_agents
    else:
        n_agents = len(contributions_list)

    # Ensure all contributions are non-negative
    if any(c < 0 for c in contributions_list):
        logger.warning("Negative contributions detected; clamping to zero")
        contributions_list = [max(0.0, c) for c in contributions_list]

    # Compute statistics
    total = sum(contributions_list)
    if total == 0:
        # All contributions are zero - perfect equality by default
        return 0.0, SpecializationMetrics(
            specialization_index=0.0,
            gini_coefficient=0.0,
            shannon_entropy=0.0,
            max_contribution=0.0,
            min_contribution=0.0,
            mean_contribution=0.0,
            std_contribution=0.0,
            validation_passed=True,
            validation_message="All contributions are zero"
        )

    # Normalize to probabilities
    probabilities = [c / total for c in contributions_list]

    # Compute Gini coefficient (primary metric for specialization)
    gini = compute_gini_coefficient(contributions_list)

    # Compute Shannon entropy (alternative perspective)
    entropy = compute_shannon_entropy(contributions_list)

    # Normalize entropy to [0, 1] range
    max_entropy = math.log(n_agents) if n_agents > 1 else 0.0
    normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0.0

    # Specialization index: use Gini as primary, but can also blend with entropy
    # Higher Gini = higher specialization
    specialization_index = gini

    # Ensure bounds [0, 1]
    specialization_index = max(0.0, min(1.0, specialization_index))

    # Compute additional statistics
    mean_contrib = total / n_agents
    std_contrib = np.std(contributions_list) if len(contributions_list) > 1 else 0.0

    metrics = SpecializationMetrics(
        specialization_index=specialization_index,
        gini_coefficient=gini,
        shannon_entropy=entropy,
        max_contribution=max(contributions_list),
        min_contribution=min(contributions_list),
        mean_contribution=mean_contrib,
        std_contribution=std_contrib,
        validation_passed=True,
        validation_message="Computation successful"
    )

    # Validation: check bounds
    if not (0.0 <= specialization_index <= 1.0):
        logger.error(f"Specialization index {specialization_index} out of bounds [0, 1]")
        metrics.validation_passed = False
        metrics.validation_message = f"Index {specialization_index} out of bounds"

    return specialization_index, metrics


def validate_specialization_index(index: float) -> Tuple[bool, str]:
    """Validate that a specialization index is within acceptable bounds.

    Args:
        index: The specialization index value to validate.

    Returns:
        Tuple of (is_valid, message)
    """
    if index < 0.0:
        return False, f"Specialization index {index} is negative"
    if index > 1.0:
        return False, f"Specialization index {index} exceeds maximum of 1.0"
    if math.isnan(index):
        return False, "Specialization index is NaN"
    if math.isinf(index):
        return False, "Specialization index is infinite"
    return True, "Valid"


def batch_compute_specialization(
    contributions_batch: List[Union[List[float], Dict[str, float]]]
) -> List[Tuple[float, SpecializationMetrics]]:
    """Compute specialization index for a batch of contribution sets.

    Args:
        contributions_batch: List of contribution sets (each can be list or dict).

    Returns:
        List of (specialization_index, metrics) tuples.
    """
    results = []
    for contributions in contributions_batch:
        idx, metrics = compute_specialization_index(contributions)
        results.append((idx, metrics))
    return results


def compute_specialization_index_v1(
    agent_skills: Union[List[float], Dict[str, float], Any, None],
    num_agents: Optional[int] = None
) -> Tuple[float, SpecializationMetrics]:
    """Legacy alias for compute_specialization_index (v1 compatibility).

    This function is provided for backward compatibility with earlier code
    that used the v1 naming convention.

    Args:
        agent_skills: Same as agent_contributions in compute_specialization_index.
        num_agents: Same as in compute_specialization_index.

    Returns:
        Same as compute_specialization_index.
    """
    return compute_specialization_index(agent_skills, num_agents)