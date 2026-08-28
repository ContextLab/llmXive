"""
Resampling module for assessing regression coefficient sensitivity.

This module handles the generation of random observation subsets across
sample size tiers, fitting OLS models, and computing empirical standard
deviations of coefficients.
"""

from .engine import run_resampling_experiment, generate_subsets, fit_ols_model
from .aggregator import calculate_coefficient_variance, compute_convergence_metrics

__all__ = [
    "run_resampling_experiment",
    "generate_subsets",
    "fit_ols_model",
    "calculate_coefficient_variance",
    "compute_convergence_metrics",
]