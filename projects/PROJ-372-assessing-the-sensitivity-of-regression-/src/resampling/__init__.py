"""
Resampling module for assessing regression coefficient sensitivity.

This module provides utilities for generating random dataset subsets,
fitting OLS models on those subsets, and aggregating stability metrics.

Exposed API:
- run_resampling_experiment: Main pipeline entry point
- generate_subsets: Subset generation logic
- fit_ols_subset: Robust OLS fitting with singularity handling
- compute_stability_metrics: Aggregation of coefficient variances
"""

from src.resampling.engine import generate_subsets, fit_ols_subset, run_resampling_experiment
from src.resampling.aggregator import compute_stability_metrics, check_convergence

__all__ = [
    "run_resampling_experiment",
    "generate_subsets",
    "fit_ols_subset",
    "compute_stability_metrics",
    "check_convergence",
]