import os
import numpy as np
from typing import Dict, List, Tuple, Any, Optional

# ============================================================================
# Global Configuration & Constants
# ============================================================================

# Random Seed for reproducibility
_SEED = 42

# Statistical Thresholds
_VIF_THRESHOLD = 5.0
_SIGNIFICANCE_LEVEL = 0.05
_STABILITY_THRESHOLD = 0.15  # Max allowed coefficient variation (%)

# Sample Size Constraints
_MIN_SAMPLE_SIZE = 100

# Perceived Social Validation (PSV) Weights (FR-008)
# Defined based on theoretical weighting of engagement vs. sentiment
_PSV_WEIGHTS = {
    'like_weight': 0.25,
    'comment_weight': 0.40,
    'share_weight': 0.35,
    'sentiment_scale': 1.0,  # Multiplier for sentiment score contribution
    'log_transform': True,   # Apply log(1+x) to engagement counts
}

# Causal Language Triggers (for FR-006)
_CAUSAL_TRIGGERS = [
    "causes", "leads to", "results in", "creates", "induces",
    "generates", "produces", "drives", "forces", "makes",
    "determines", "guarantees", "ensures", "provokes", "triggers"
]

# ============================================================================
# Accessor Functions
# ============================================================================

def get_seed() -> int:
    """Return the global random seed."""
    return _SEED

def get_vif_threshold() -> float:
    """Return the VIF threshold for multicollinearity detection."""
    return _VIF_THRESHOLD

def get_significance_level() -> float:
    """Return the significance level (alpha)."""
    return _SIGNIFICANCE_LEVEL

def get_stability_threshold() -> float:
    """Return the stability threshold for coefficient variation."""
    return _STABILITY_THRESHOLD

def get_min_sample_size() -> int:
    """Return the minimum required sample size."""
    return _MIN_SAMPLE_SIZE

def get_psv_weights() -> Dict[str, Any]:
    """
    Return the weights and logic for the 'Perceived Social Validation'
    measurement model as defined in FR-008.

    Formula:
    PSV = (w_like * log(1 + likes) + w_comment * log(1 + comments) + w_share * log(1 + shares))
          * sentiment_score * sentiment_scale

    Where:
    - w_like = 0.25
    - w_comment = 0.40
    - w_share = 0.35
    - sentiment_scale = 1.0
    - log_transform = True (applies log(1+x) to engagement counts)

    Returns:
        Dict containing keys: 'like_weight', 'comment_weight', 'share_weight',
        'sentiment_scale', 'log_transform'.
    """
    return _PSV_WEIGHTS.copy()

def is_significant(p_value: float) -> bool:
    """Check if a p-value is below the significance threshold."""
    return p_value < get_significance_level()

def check_vif(vif_value: float) -> Tuple[bool, str]:
    """
    Check if a VIF value exceeds the threshold.

    Returns:
        Tuple of (is_pass, status_string)
        is_pass: True if VIF <= threshold
        status_string: "PASS" or "FAIL"
    """
    threshold = get_vif_threshold()
    if vif_value <= threshold:
        return True, "PASS"
    return False, "FAIL"

def check_stability(variation: float) -> Tuple[bool, str]:
    """
    Check if coefficient variation exceeds the stability threshold.

    Returns:
        Tuple of (is_pass, status_string)
        is_pass: True if variation <= threshold
        status_string: "PASS" or "FAIL"
    """
    threshold = get_stability_threshold()
    if variation <= threshold:
        return True, "PASS"
    return False, "FAIL"

def get_causal_triggers() -> List[str]:
    """Return the list of causal trigger words."""
    return _CAUSAL_TRIGGERS.copy()

# ============================================================================
# End of Constants
# ============================================================================