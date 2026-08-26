"""
Resampling module for User Story 2.

Provides functionality for generating random observation subsets,
fitting OLS models, and computing empirical standard deviation of coefficients.
"""
from .engine import run_resampling_experiment
from .aggregator import (
    calculate_empirical_sd,
    load_resampling_results,
    run_aggregation_pipeline
)

__all__ = [
    'run_resampling_experiment',
    'calculate_empirical_sd',
    'load_resampling_results',
    'run_aggregation_pipeline'
]
