"""
Resampling module for subset generation and stability estimation.

This module handles the generation of random observation subsets across
defined sample size tiers and the fitting of OLS models to estimate
coefficient stability.

Public API:
- run_resampling_experiment: Main entry point for the resampling pipeline.
"""

from .engine import run_resampling_experiment
from .aggregator import calculate_coefficient_stability

__all__ = [
    "run_resampling_experiment",
    "calculate_coefficient_stability",
]