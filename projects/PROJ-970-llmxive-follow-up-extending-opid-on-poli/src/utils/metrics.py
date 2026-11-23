"""
Metric utilities used across the project.

Functions:
  - ``entropy(probs)`` – Shannon entropy of a probability vector.
  - ``log_prob_shift(original, injected)`` – compute the log‑probability
    shift introduced by OPID injection.
  - ``episode_statistics(episode_dict)`` – produce a dict conforming to
    ``episode_result.schema.yaml`` (placeholder implementation; actual
    schema validation is performed elsewhere).
"""

import math
from typing import Dict, Any

def entropy(probs):
    """Shannon entropy of a probability vector (base e)."""
    if not probs:
        return 0.0
    return -sum(p * math.log(p) for p in probs if p > 0)

def log_prob_shift(original, injected):
    """Return the log‑probability shift introduced by injection."""
    return math.log(injected) - math.log(original) if original > 0 else 0.0

def episode_statistics(episode_result):
    """Return a dict matching the episode_result schema (simplified)."""
    # This placeholder assumes ``episode_result`` already contains the
    # required keys. In a full implementation the schema would be validated
    # here.
    return dict(episode_result)