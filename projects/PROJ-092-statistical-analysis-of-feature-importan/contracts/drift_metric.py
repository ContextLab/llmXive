"""
Drift Metric Schema Definitions.

Defines the structure for storing drift metrics calculated
between consecutive time windows.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime


@dataclass
class DriftMetric:
    """
    Schema for drift metrics between two consecutive windows.
    
    Attributes:
        transition_id: Unique identifier for the transition (e.g., 'T1_T2')
        window_t: ID of the earlier window (source)
        window_t_plus_1: ID of the later window (target)
        spearman_rho: Spearman rank correlation coefficient
        p_value: P-value for the Spearman correlation
        is_significant: Boolean indicating if correlation is statistically significant
        drift_magnitude: Absolute value of spearman_rho
        trend_direction: 'stable', 'increase', or 'decrease' based on rho
        null_baseline_mean: Mean rho from the null baseline (if available)
        deviation_from_null: Difference between observed rho and null baseline mean
        block_permutation_p_value: P-value from block permutation test
        is_high_drift: Boolean flag if drift is significant (p < 0.05)
        calculation_date: ISO timestamp when drift was calculated
    """
    transition_id: str
    window_t: str
    window_t_plus_1: str
    spearman_rho: float
    p_value: float
    is_significant: bool = False
    drift_magnitude: float = 0.0
    trend_direction: str = "stable"
    null_baseline_mean: Optional[float] = None
    deviation_from_null: Optional[float] = None
    block_permutation_p_value: Optional[float] = None
    is_high_drift: bool = False
    calculation_date: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def __post_init__(self):
        """Post-initialization logic to derive derived fields."""
        self.drift_magnitude = abs(self.spearman_rho)
        
        if self.spearman_rho > 0.05:
            self.trend_direction = "increase"
        elif self.spearman_rho < -0.05:
            self.trend_direction = "decrease"
        else:
            self.trend_direction = "stable"
        
        if self.block_permutation_p_value is not None:
            self.is_high_drift = self.block_permutation_p_value < 0.05

    def to_dict(self) -> dict:
        """Convert the dataclass instance to a dictionary."""
        return {
            "transition_id": self.transition_id,
            "window_t": self.window_t,
            "window_t_plus_1": self.window_t_plus_1,
            "spearman_rho": self.spearman_rho,
            "p_value": self.p_value,
            "is_significant": self.is_significant,
            "drift_magnitude": self.drift_magnitude,
            "trend_direction": self.trend_direction,
            "null_baseline_mean": self.null_baseline_mean,
            "deviation_from_null": self.deviation_from_null,
            "block_permutation_p_value": self.block_permutation_p_value,
            "is_high_drift": self.is_high_drift,
            "calculation_date": self.calculation_date
        }
