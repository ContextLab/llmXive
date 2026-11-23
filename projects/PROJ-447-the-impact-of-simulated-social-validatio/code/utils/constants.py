"""
Configuration constants and utility functions for the research pipeline.

This module centralizes all configurable parameters including seeds, thresholds,
measurement model weights, and validation rules.
"""

import os
import numpy as np
from typing import Dict, List, Tuple, Any, Optional

# Default values
_DEFAULT_SEED = 42
_DEFAULT_VIF_THRESHOLD = 5.0
_DEFAULT_SIGNIFICANCE_LEVEL = 0.05
_DEFAULT_STABILITY_THRESHOLD = 0.1
_DEFAULT_MIN_SAMPLE_SIZE = 100

# PSV Weights (from T015a)
_PSV_WEIGHTS = {
    "likes": 0.6,
    "sentiment": 0.4
}

# Causal trigger words (from T006)
_CAUSAL_TRIGGERS = [
    "causes", "leads to", "results in", "determines", "influences",
    "effects", "drives", "triggers", "induces", "generates"
]

# Global configuration store
_config: Dict[str, Any] = {
    "seed": _DEFAULT_SEED,
    "vif_threshold": _DEFAULT_VIF_THRESHOLD,
    "significance_level": _DEFAULT_SIGNIFICANCE_LEVEL,
    "stability_threshold": _DEFAULT_STABILITY_THRESHOLD,
    "min_sample_size": _DEFAULT_MIN_SAMPLE_SIZE,
    "psv_weights": _PSV_WEIGHTS,
    "causal_triggers": _CAUSAL_TRIGGERS
}


def set_seed(seed: int) -> None:
    """Set the global random seed."""
    _config["seed"] = seed
    np.random.seed(seed)


def get_seed() -> int:
    """Get the current random seed."""
    return _config["seed"]


def get_vif_threshold() -> float:
    """Get the VIF threshold."""
    return _config["vif_threshold"]


def get_significance_level() -> float:
    """Get the significance level (alpha)."""
    return _config["significance_level"]


def get_stability_threshold() -> float:
    """Get the stability threshold for coefficient variation."""
    return _config["stability_threshold"]


def get_min_sample_size() -> int:
    """Get the minimum required sample size."""
    return _config["min_sample_size"]


def get_psv_weights() -> Dict[str, float]:
    """Get the weights for Perceived Social Validation calculation."""
    return _config["psv_weights"].copy()


def get_causal_triggers() -> List[str]:
    """Get the list of causal trigger words."""
    return _config["causal_triggers"].copy()


def is_significant(p_value: float, alpha: Optional[float] = None) -> bool:
    """
    Check if a p-value is significant.

    Args:
        p_value: The p-value to check.
        alpha: Optional significance level. Defaults to config.

    Returns:
        True if p_value < alpha.
    """
    if alpha is None:
        alpha = get_significance_level()
    return p_value < alpha


def check_vif(vif_value: float, threshold: Optional[float] = None) -> bool:
    """
    Check if a VIF value is within acceptable limits.

    Args:
        vif_value: The VIF value to check.
        threshold: Optional threshold. Defaults to config.

    Returns:
        True if vif_value <= threshold.
    """
    if threshold is None:
        threshold = get_vif_threshold()
    return vif_value <= threshold


def check_stability(variation: float, threshold: Optional[float] = None) -> bool:
    """
    Check if coefficient variation is within the stability threshold.

    Args:
        variation: The calculated variation.
        threshold: Optional threshold. Defaults to config.

    Returns:
        True if variation <= threshold.
    """
    if threshold is None:
        threshold = get_stability_threshold()
    return variation <= threshold
