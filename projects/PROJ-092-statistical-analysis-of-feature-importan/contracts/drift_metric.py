"""
Data schema definitions for the drift_metric entity.
Defines the structure for drift measurements between windows.
"""
from dataclasses import dataclass
from typing import Optional
from enum import Enum


class DriftType(Enum):
    """Type of drift detected."""
    CONCEPT = "concept"
    COVARIATE = "covariate"
    DATA_DRIFT = "data_drift"


@dataclass
class RankCorrelationMetric:
    """
    Schema for Spearman rank correlation between two windows.
    """
    window_t: int
    window_t_plus_1: int
    rho: float
    p_value: float
    significant_at_005: bool = False
    magnitude: str = "none"  # none, low, medium, high

    def __post_init__(self):
        """Classify magnitude based on |rho| deviation from 1."""
        deviation = abs(1.0 - abs(self.rho))
        if deviation < 0.1:
            self.magnitude = "none"
        elif deviation < 0.3:
            self.magnitude = "low"
        elif deviation < 0.5:
            self.magnitude = "medium"
        else:
            self.magnitude = "high"
        
        self.significant_at_005 = self.p_value < 0.05

@dataclass
class TrendMetric:
    """
    Schema for Mann-Kendall trend test results.
    """
    sequence_type: str  # e.g., "rho_sequence"
    kendall_tau: float
    p_value: float
    trend_direction: str  # "increasing", "decreasing", "no_trend"
    sample_size: int
    is_significant: bool = False

    def __post_init__(self):
        """Determine trend direction and significance."""
        if self.kendall_tau > 0.1:
            self.trend_direction = "increasing"
        elif self.kendall_tau < -0.1:
            self.trend_direction = "decreasing"
        else:
            self.trend_direction = "no_trend"
        
        self.is_significant = self.p_value < 0.05

@dataclass
class NullBaselineResult:
    """
    Schema for Null Model Baseline results.
    """
    mean_rho: float
    std_rho: float
    n_permutations: int
    observed_rho_mean: float
    z_score: float
    p_value: float

@dataclass
class GlobalStats:
    """
    Schema for aggregated global statistics.
    """
    mean_rho: float
    trend_direction: str
    p_value: float
    stable_window_count: int
    total_windows: int
    model_failures: int
    avg_model_r_squared: Optional[float] = None
    high_drift_count: int = 0
