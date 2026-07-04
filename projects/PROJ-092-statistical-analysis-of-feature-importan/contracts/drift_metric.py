"""
Drift metric schema definitions.
Defines the structure for Spearman correlation and statistical significance results.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class DriftMetric:
    """
    Represents a single drift measurement between two consecutive windows.
    """
    window_t: int
    window_t_plus_1: int
    spearman_rho: float
    p_value: float
    is_significant: bool = False
    drift_magnitude: str = "low"  # low, medium, high

@dataclass
class NullBaselineResult:
    """
    Result of the null model baseline experiment.
    """
    mean_rho: float
    std_rho: float
    num_permutations: int
    method: str = "chronological_shuffle"

@dataclass
class SignificanceTestResult:
    """
    Result of the Mann-Kendall trend test and block permutation test.
    """
    kendall_tau: float
    trend_direction: str  # "monotonic increase", "monotonic decrease", "no trend"
    block_permutation_p_value: float
    is_trend_significant: bool
    sample_size: int
