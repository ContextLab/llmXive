"""
Specialization Index Computation for Social Memory Networks.

This module implements the calculation of the specialization index, a distribution-based
metric that quantifies the degree of specialization among agents in a multi-agent system.
It also provides utilities for Gini coefficient and Shannon entropy calculations.
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
    """Container for specialization-related metrics."""
    specialization_index: float
    gini_coefficient: float
    shannon_entropy: float
    max_contribution_ratio: float
    total_contributions: int
    effective_agents: int  # Number of agents with non-zero contributions
    validation_status: str = "unknown"
    validation_message: str = ""


def compute_gini_coefficient(values: List[float]) -> float:
    """
    Compute the Gini coefficient for a list of values.

    The Gini coefficient measures inequality among values in a frequency distribution.
    A value of 0 represents perfect equality (all values are the same), while 1
    represents maximal inequality (one value is non-zero, others are zero).

    Args:
        values: List of non-negative numeric values.

    Returns:
        Gini coefficient in the range [0, 1].
    """
    if not values or all(v == 0 for v in values):
        return 0.0

    n = len(values)
    sorted_values = sorted(values)
    cumsum = np.cumsum(sorted_values)

    # Gini formula: G = (2 * sum(i * y_i) - (n + 1) * sum(y_i)) / (n * sum(y_i))
    numerator = 2 * np.sum((np.arange(1, n + 1) * sorted_values))
    denominator = n * np.sum(sorted_values)

    if denominator == 0:
        return 0.0

    gini = (numerator - (n + 1) * np.sum(sorted_values)) / denominator
    return max(0.0, min(1.0, gini))


def compute_shannon_entropy(values: List[float]) -> float:
    """
    Compute the Shannon entropy for a list of values.

    Shannon entropy measures the uncertainty or randomness in a distribution.
    Higher entropy indicates more uniform distribution (less specialization).

    Args:
        values: List of non-negative numeric values.

    Returns:
        Shannon entropy value (non-negative).
    """
    if not values or all(v == 0 for v in values):
        return 0.0

    total = sum(values)
    if total == 0:
        return 0.0

    probabilities = [v / total for v in values if v > 0]

    if not probabilities:
        return 0.0

    entropy = -sum(p * math.log(p) if p > 0 else 0 for p in probabilities)
    return entropy


def compute_specialization_index(
    contributions: Union[List[Union[int, float]], Dict[str, Union[int, float]], None],
    num_agents: Optional[int] = None
) -> Tuple[float, SpecializationMetrics]:
    """
    Compute the specialization index based on per-agent fact contributions.

    The specialization index measures how unevenly facts/contributions are distributed
    among agents. A higher index indicates greater specialization (some agents
    contribute significantly more than others).

    The index is calculated as: 1 - (Shannon entropy / max possible entropy)
    This normalizes the entropy to [0, 1], where 0 means perfect equality
    (no specialization) and 1 means maximal specialization.

    Args:
        contributions: Per-agent contribution counts. Can be:
            - List of numbers (indexed by agent)
            - Dict mapping agent identifiers to contribution counts
            - None (treated as all zeros)
        num_agents: Optional explicit number of agents. If None, inferred from
            the input data.

    Returns:
        Tuple of (specialization_index, SpecializationMetrics object).
        The specialization_index is bounded in [0, 1].
    """
    # Handle None input
    if contributions is None:
        contributions = []

    # Normalize input to list of floats
    if isinstance(contributions, dict):
        contrib_list = list(contributions.values())
    elif isinstance(contributions, list):
        contrib_list = [float(c) for c in contributions]
    else:
        # Single value case
        contrib_list = [float(contributions)] if contributions is not None else []

    # Handle empty list
    if not contrib_list:
        logger.warning("Empty contributions provided; returning zero specialization")
        metrics = SpecializationMetrics(
            specialization_index=0.0,
            gini_coefficient=0.0,
            shannon_entropy=0.0,
            max_contribution_ratio=0.0,
            total_contributions=0,
            effective_agents=0,
            validation_status="warning",
            validation_message="Empty contributions provided"
        )
        return 0.0, metrics

    # Ensure non-negative
    contrib_list = [max(0.0, c) for c in contrib_list]

    # Determine number of agents
    n_agents = num_agents if num_agents is not None else len(contrib_list)

    # Pad with zeros if num_agents > len(contrib_list)
    if n_agents > len(contrib_list):
        contrib_list.extend([0.0] * (n_agents - len(contrib_list)))
    elif n_agents < len(contrib_list):
        # Truncate if num_agents < len(contrib_list)
        logger.warning(f"num_agents ({n_agents}) < len(contributions) ({len(contrib_list)}); truncating")
        contrib_list = contrib_list[:n_agents]

    # Compute total contributions
    total_contributions = sum(contrib_list)

    # Count effective agents (non-zero contributions)
    effective_agents = sum(1 for c in contrib_list if c > 0)

    # Compute metrics
    gini = compute_gini_coefficient(contrib_list)
    entropy = compute_shannon_entropy(contrib_list)

    # Max possible entropy is log(n_agents) when all agents contribute equally
    max_entropy = math.log(n_agents) if n_agents > 1 else 0.0

    # Specialization index: 1 - (entropy / max_entropy)
    # This gives 0 for uniform distribution, 1 for maximal specialization
    if max_entropy > 0 and entropy > 0:
        specialization_index = 1.0 - (entropy / max_entropy)
    else:
        # If entropy is 0 (one agent has all contributions) or max_entropy is 0 (1 agent)
        if total_contributions > 0 and effective_agents == 1:
            specialization_index = 1.0  # Maximal specialization
        else:
            specialization_index = 0.0  # No specialization (uniform or empty)

    # Ensure bounds [0, 1]
    specialization_index = max(0.0, min(1.0, specialization_index))

    # Compute max contribution ratio
    max_contribution = max(contrib_list) if contrib_list else 0.0
    max_contribution_ratio = max_contribution / total_contributions if total_contributions > 0 else 0.0

    # Validation
    validation_status = "passed"
    validation_message = ""

    if specialization_index < 0 or specialization_index > 1:
        validation_status = "failed"
        validation_message = f"Specialization index {specialization_index} out of bounds [0, 1]"
        logger.error(f"Validation failed: {validation_message}")
    elif gini < 0 or gini > 1:
        validation_status = "failed"
        validation_message = f"Gini coefficient {gini} out of bounds [0, 1]"
        logger.error(f"Validation failed: {validation_message}")
    elif total_contributions < 0:
        validation_status = "failed"
        validation_message = f"Total contributions {total_contributions} is negative"
        logger.error(f"Validation failed: {validation_message}")
    else:
        logger.info(f"Specialization index computed: {specialization_index:.4f} (Gini: {gini:.4f}, Entropy: {entropy:.4f})")

    metrics = SpecializationMetrics(
        specialization_index=specialization_index,
        gini_coefficient=gini,
        shannon_entropy=entropy,
        max_contribution_ratio=max_contribution_ratio,
        total_contributions=int(total_contributions),
        effective_agents=effective_agents,
        validation_status=validation_status,
        validation_message=validation_message
    )

    return specialization_index, metrics


def validate_specialization_index(index: float, metrics: Optional[SpecializationMetrics] = None) -> bool:
    """
    Validate that a specialization index is within acceptable bounds.

    Args:
        index: The specialization index value to validate.
        metrics: Optional SpecializationMetrics object for additional context.

    Returns:
        True if the index is valid (in [0, 1]), False otherwise.
    """
    if index < 0 or index > 1:
        logger.error(f"Invalid specialization index: {index} (must be in [0, 1])")
        return False

    if metrics is not None:
        if metrics.validation_status == "failed":
            logger.error(f"Metrics validation failed: {metrics.validation_message}")
            return False

    return True


def batch_compute_specialization(
    contribution_batches: List[Union[List[float], Dict[str, float]]]
) -> List[Tuple[float, SpecializationMetrics]]:
    """
    Compute specialization index for multiple batches of contributions.

    Args:
        contribution_batches: List of contribution lists/dicts, one per batch/game.

    Returns:
        List of (specialization_index, metrics) tuples for each batch.
    """
    results = []
    for batch_idx, contributions in enumerate(contribution_batches):
        try:
            idx, metrics = compute_specialization_index(contributions)
            results.append((idx, metrics))
        except Exception as e:
            logger.error(f"Error computing specialization for batch {batch_idx}: {e}")
            # Return zero specialization for failed batches
            metrics = SpecializationMetrics(
                specialization_index=0.0,
                gini_coefficient=0.0,
                shannon_entropy=0.0,
                max_contribution_ratio=0.0,
                total_contributions=0,
                effective_agents=0,
                validation_status="failed",
                validation_message=str(e)
            )
            results.append((0.0, metrics))

    return results


def compute_specialization_index_v1(
    agent_skills: List[int],
    num_agents: int
) -> Tuple[float, SpecializationMetrics]:
    """
    Legacy alias for compute_specialization_index (v1 compatibility).

    This function maintains compatibility with earlier versions of the API
    that expected (agent_skills, num_agents) as parameters.

    Args:
        agent_skills: List of skill/contribution counts per agent.
        num_agents: Number of agents (used for padding if len(agent_skills) < num_agents).

    Returns:
        Tuple of (specialization_index, SpecializationMetrics).
    """
    return compute_specialization_index(agent_skills, num_agents=num_agents)