"""Specialization index metrics for transactive memory systems."""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, List, Tuple, Optional, Union

import numpy as np


@dataclass
class SpecializationMetrics:
    """Metrics related to knowledge specialization."""
    gini_coefficient: float = 0.0
    shannon_entropy: float = 0.0
    specialization_index: float = 0.0
    skill_variance: float = 0.0


def compute_gini_coefficient(values: List[float]) -> float:
    """Computes the Gini coefficient for a list of values."""
    if not values or len(values) == 0:
        return 0.0
    
    n = len(values)
    if n == 1:
        return 0.0
    
    sorted_values = sorted(values)
    cumsum = np.cumsum(sorted_values)
    
    # Gini formula: (2 * sum(i * x_i) - (n+1) * sum(x_i)) / (n * sum(x_i))
    numerator = 2 * np.sum((np.arange(1, n + 1) * sorted_values))
    denominator = n * cumsum[-1]
    
    if denominator == 0:
        return 0.0
        
    gini = (numerator - (n + 1) * cumsum[-1]) / denominator
    return float(gini)


def compute_shannon_entropy(values: List[float]) -> float:
    """Computes Shannon entropy for a distribution of values."""
    if not values or sum(values) == 0:
        return 0.0
    
    total = sum(values)
    probs = [v / total for v in values if v > 0]
    
    entropy = 0.0
    for p in probs:
        if p > 0:
            entropy -= p * math.log(p)
    
    return entropy


def compute_specialization_index(
    agent_skills: Union[List[int], List[float], int],
    num_agents: Optional[int] = None
) -> Tuple[float, SpecializationMetrics]:
    """
    Computes the specialization index based on the distribution of skills/knowledge.
    
    Handles multiple call signatures:
    1. compute_specialization_index(agent_skills, num_agents=N) - standard
    2. compute_specialization_index(agent_skills=[...], num_agents=3) - keyword
    3. Legacy: if agent_skills is an int, treat as count (deprecated, returns 0)
    
    Returns:
        Tuple of (specialization_index, SpecializationMetrics)
    """
    # Handle legacy call: compute_specialization_index(5, 10) -> agent_skills=5, num_agents=10
    # This is ambiguous. If agent_skills is int, assume it's a count of something else?
    # The spec says agent_skills is a list. If it's an int, we treat it as a degenerate case.
    if isinstance(agent_skills, int):
        # Legacy/erroneous call: treat as 0 specialization
        return 0.0, SpecializationMetrics()
        
    if not isinstance(agent_skills, list):
        return 0.0, SpecializationMetrics()

    if not agent_skills:
        return 0.0, SpecializationMetrics()

    # If num_agents is not provided, infer from list length
    if num_agents is None:
        num_agents = len(agent_skills)
    
    # Ensure we only use the first num_agents if list is longer
    skills = agent_skills[:num_agents]
    
    # Calculate metrics
    gini = compute_gini_coefficient(skills)
    entropy = compute_shannon_entropy(skills)
    
    # Specialization Index: A weighted combination.
    # High Gini = High specialization (unequal distribution)
    # Low Entropy = High specialization (predictable distribution)
    # We normalize entropy by max possible entropy (log(N))
    max_entropy = math.log(num_agents) if num_agents > 1 else 1.0
    normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0.0
    
    # Index = Gini * (1 - Normalized_Entropy)
    # If Gini is high (0-1) and Entropy is low (0-1), Index is high.
    spec_index = gini * (1.0 - normalized_entropy)
    
    # Clamp to [0, 1]
    spec_index = max(0.0, min(1.0, spec_index))
    
    metrics = SpecializationMetrics(
        gini_coefficient=gini,
        shannon_entropy=entropy,
        specialization_index=spec_index,
        skill_variance=float(np.var(skills)) if skills else 0.0
    )
    
    return spec_index, metrics


def validate_specialization_index(index: float) -> Tuple[bool, str]:
    if not (0.0 <= index <= 1.0):
        return False, f"Specialization index {index} out of range [0, 1]"
    return True, "OK"


def batch_compute_specialization(results: List[Dict[str, Any]]) -> List[float]:
    """Computes specialization index for a batch of game results."""
    indices = []
    for res in results:
        skills = res.get("agent_skills", [])
        n = res.get("agent_count", len(skills))
        idx, _ = compute_specialization_index(skills, num_agents=n)
        indices.append(idx)
    return indices
