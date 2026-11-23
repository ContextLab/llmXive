"""
Global Statistics Schema Definitions.

Defines the structure for aggregated statistics across all windows
and drift metrics.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class GlobalStats:
    """
    Schema for aggregated global statistics.
    
    Attributes:
        total_windows_processed: Total number of windows processed
        valid_window_count: Number of windows meeting R2 threshold
        mean_r2: Average R2 score of valid windows
        mean_rho: Average Spearman rho across all transitions
        trend_direction: Overall trend direction ('stable', 'increase', 'decrease')
        p_value: Overall significance p-value (from Mann-Kendall or permutation)
        stable_window_count: Count of windows with stable importance profiles
        high_drift_transitions: List of transition IDs flagged as high drift
        null_baseline_mean: Mean rho from null baseline analysis
        analysis_start_time: ISO timestamp when analysis started
        analysis_end_time: ISO timestamp when analysis ended
        report_version: Version of the report format
    """
    total_windows_processed: int = 0
    valid_window_count: int = 0
    mean_r2: Optional[float] = None
    mean_rho: Optional[float] = None
    trend_direction: str = "stable"
    p_value: Optional[float] = None
    stable_window_count: int = 0
    high_drift_transitions: List[str] = field(default_factory=list)
    null_baseline_mean: Optional[float] = None
    analysis_start_time: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    analysis_end_time: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    report_version: str = "1.0"

    def to_dict(self) -> dict:
        """Convert the dataclass instance to a dictionary."""
        return {
            "total_windows_processed": self.total_windows_processed,
            "valid_window_count": self.valid_window_count,
            "mean_r2": self.mean_r2,
            "mean_rho": self.mean_rho,
            "trend_direction": self.trend_direction,
            "p_value": self.p_value,
            "stable_window_count": self.stable_window_count,
            "high_drift_transitions": self.high_drift_transitions,
            "null_baseline_mean": self.null_baseline_mean,
            "analysis_start_time": self.analysis_start_time,
            "analysis_end_time": self.analysis_end_time,
            "report_version": self.report_version
        }