"""Specialization metrics computation."""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, List, Tuple, Optional, Union

import numpy as np


@dataclass
class SpecializationMetrics:
    gini: float = 0.0
    entropy: float = 0.0
    specialization_index: float = 0.0


def compute_gini_coefficient(values: List[float]) -> float:
    """Compute Gini coefficient for a list of values."""
    if not values or sum(values) == 0:
        return 0.0
    sorted_values = sorted(values)
    n = len(sorted_values)
    cumsum = np.cumsum(sorted_values)
    return (n + 1 - 2 * np.sum(cumsum) / cumsum[-1]) / n


def compute_shannon_entropy(values: List[float]) -> float:
    """Compute Shannon entropy for a list of values."""
    total = sum(values)
    if total == 0:
        return 0.0
    probs = [v / total for v in values if v > 0]
    if not probs:
        return 0.0
    return -sum(p * math.log(p) for p in probs)


def compute_specialization_index(
    agent_skills: Union[List[int], List[float]], 
    num_agents: Optional[int] = None
) -> Tuple[float, SpecializationMetrics]:
    """
    Compute the specialization index based on the distribution of facts/skills.
    
    Handles multiple call signatures for compatibility.
    """
    # Normalize input
    if isinstance(agent_skills, int):
        # Legacy: treat as count, generate dummy distribution
        agent_skills = [1] * agent_skills
    
    if not agent_skills:
        return 0.0, SpecializationMetrics()
    
    if num_agents is None:
        num_agents = len(agent_skills)
    
    # Ensure list length matches num_agents if provided
    if len(agent_skills) != num_agents:
        # If lengths differ, pad or truncate (simulation behavior)
        if len(agent_skills) < num_agents:
            agent_skills = list(agent_skills) + [0] * (num_agents - len(agent_skills))
        else:
            agent_skills = agent_skills[:num_agents]
    
    # Compute metrics
    gini = compute_gini_coefficient(agent_skills)
    entropy = compute_shannon_entropy(agent_skills)
    
    # Specialization Index: 1 - (Entropy / Max_Entropy)
    # Max entropy for N agents is log(N)
    max_entropy = math.log(num_agents) if num_agents > 1 else 1.0
    if max_entropy == 0:
        max_entropy = 1.0
    
    norm_entropy = entropy / max_entropy
    spec_index = 1.0 - norm_entropy
    
    # Clamp to [0, 1]
    spec_index = max(0.0, min(1.0, spec_index))
    
    metrics = SpecializationMetrics(
        gini=gini,
        entropy=entropy,
        specialization_index=spec_index
    )
    
    return spec_index, metrics


def validate_specialization_index(index: float) -> bool:
    """Validate that the index is in [0, 1]."""
    return 0.0 <= index <= 1.0


def batch_compute_specialization(results: List[Dict[str, Any]]) -> List[float]:
    """Compute specialization index for a list of game results."""
    indices = []
    for res in results:
        # Assume 'facts_per_agent' is in the result
        if "facts_per_agent" in res:
            idx, _ = compute_specialization_index(res["facts_per_agent"])
            indices.append(idx)
        else:
            indices.append(0.0)
    return indices
