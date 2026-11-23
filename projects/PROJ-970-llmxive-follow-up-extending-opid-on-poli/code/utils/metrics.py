"""
Metric utilities for OPID routing experiments.

The module provides pure‑CPU functions required by the experiment runner
and analysis scripts.  Implementations are straightforward and avoid any
external dependencies beyond the standard library and NumPy.
"""

import math
from dataclasses import dataclass
from typing import List, Tuple

import numpy as np

@dataclass
class SuccessRateResult:
    success_count: int
    total: int
    rate: float

def calculate_success_rate(trajectory: List[int], ground_truth: List[int]) -> SuccessRateResult:
    """
    Compute whether ``trajectory`` contains ``ground_truth`` as a subsequence.
    Returns a ``SuccessRateResult`` with count (0 or 1) and rate.
    """
    if not ground_truth:
        return SuccessRateResult(success_count=0, total=0, rate=0.0)

    # Simple subsequence check.
    it = iter(trajectory)
    matched = all(item in it for item in ground_truth)
    return SuccessRateResult(success_count=int(matched), total=1, rate=1.0 if matched else 0.0)

def calculate_action_entropy(actions: List[int]) -> float:
    """
    Compute Shannon entropy (base‑2) of a list of discrete actions.
    """
    if not actions:
        return 0.0
    counts = np.bincount(actions)
    probs = counts[counts > 0] / len(actions)
    return -np.sum(probs * np.log2(probs))

def calculate_raw_entropy(probabilities: List[float]) -> float:
    """
    Compute Shannon entropy given a probability distribution.
    Probabilities should sum to 1; values outside [0,1] are ignored.
    """
    probs = np.array([p for p in probabilities if p > 0])
    if probs.size == 0:
        return 0.0
    return -np.sum(probs * np.log2(probs))

def calculate_mean_entropy(entropies: List[float]) -> float:
    """Mean of a list of entropy values."""
    if not entropies:
        return 0.0
    return float(np.mean(entropies))

def calculate_variance(values: List[float]) -> float:
    """Population variance (denominator N)."""
    if not values:
        return 0.0
    return float(np.var(values))

def calculate_mean_log_prob_shift(shifts: List[float]) -> float:
    """Mean of log‑probability shift values."""
    if not shifts:
        return 0.0
    return float(np.mean(shifts))

def calculate_distillation_cost_benefit_ratio(
    mean_log_prob_shift: float,
    success_rate_held_out: float,
    baseline_success_rate: float,
) -> float:
    """
    Ratio of average log‑probability shift to improvement in success rate.
    Returns ``inf`` when denominator ≤ 0.
    """
    improvement = success_rate_held_out - baseline_success_rate
    if improvement <= 0:
        return float("inf")
    return mean_log_prob_shift / improvement
