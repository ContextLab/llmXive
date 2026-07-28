"""
Calibration module for conformal prediction and interval adjustment.

This module provides tools for calibrating predictive intervals to achieve
desired coverage levels using self-calibrating conformal prediction methods.
"""

from calibration.conformal import (
    SelfCalibratingConformalWrapper,
    compare_baseline_vs_conformal,
    aggregate_conformal_results,
    conformal_results_to_dataframe
)

__all__ = [
    "SelfCalibratingConformalWrapper",
    "compare_baseline_vs_conformal",
    "aggregate_conformal_results",
    "conformal_results_to_dataframe"
]
