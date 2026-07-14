"""
Metrics calculation module for meta-analysis estimation results.

Calculates bias, coverage, and I^2 statistics.
"""

import math
from typing import List, Dict, Any, Optional
import numpy as np
from scipy import stats

from utils.logging import get_logger

logger = get_logger(__name__)


class MetricsResult:
    """Container for calculated metrics."""
    def __init__(
        self,
        replicate_id: int,
        true_effect: float,
        pooled_estimate: float,
        ci_lower: float,
        ci_upper: float,
        tau_squared_estimate: float,
        i_squared: float,
        bias: float,
        coverage_flag: bool
    ):
        self.replicate_id = replicate_id
        self.true_effect = true_effect
        self.pooled_estimate = pooled_estimate
        self.ci_lower = ci_lower
        self.ci_upper = ci_upper
        self.tau_squared_estimate = tau_squared_estimate
        self.i_squared = i_squared
        self.bias = bias
        self.coverage_flag = coverage_flag

    def to_dict(self) -> Dict[str, Any]:
        return {
            "replicate_id": self.replicate_id,
            "true_effect": self.true_effect,
            "pooled_estimate": self.pooled_estimate,
            "ci_lower": self.ci_lower,
            "ci_upper": self.ci_upper,
            "tau_squared_estimate": self.tau_squared_estimate,
            "i_squared": self.i_squared,
            "bias": self.bias,
            "coverage_flag": self.coverage_flag
        }


def calculate_bias(pooled_estimate: float, true_effect: float) -> float:
    """Calculates the bias of the pooled estimate."""
    return pooled_estimate - true_effect


def calculate_coverage(
    ci_lower: float,
    ci_upper: float,
    true_effect: float
) -> bool:
    """Checks if the true effect is within the confidence interval."""
    return ci_lower <= true_effect <= ci_upper


def calculate_i_squared(
    effect_sizes: List[float],
    standard_errors: List[float],
    pooled_estimate: float
) -> float:
    """
    Calculates the I^2 statistic.
    I^2 = max(0, (Q - df) / Q) * 100
    where Q = sum(w_i * (y_i - pooled)^2) and df = k - 1
    """
    k = len(effect_sizes)
    if k < 2:
        return 0.0

    # Weights (inverse variance)
    # For I^2 calculation in RE context, we often use fixed weights or specific formulas.
    # Using standard inverse variance weights for Q statistic calculation.
    weights = [1.0 / (se**2) for se in standard_errors]

    # Q statistic
    q = sum(w * (y - pooled_estimate)**2 for w, y in zip(weights, effect_sizes))
    df = k - 1

    if q <= df:
        return 0.0

    i_squared = (q - df) / q
    return i_squared * 100.0


def aggregate_metrics(
    results: List[MetricsResult],
    true_effect: float
) -> Dict[str, Any]:
    """
    Aggregates metrics across all replicates.
    Calculates mean bias, coverage rate, and mean I^2.
    """
    if not results:
        return {
            "mean_bias": 0.0,
            "coverage_rate": 0.0,
            "mean_i_squared": 0.0,
            "total_replicates": 0
        }

    biases = [r.bias for r in results]
    coverage_flags = [1.0 if r.coverage_flag else 0.0 for r in results]
    i_squares = [r.i_squared for r in results]

    return {
        "mean_bias": float(np.mean(biases)),
        "coverage_rate": float(np.mean(coverage_flags)),
        "mean_i_squared": float(np.mean(i_squares)),
        "total_replicates": len(results)
    }
