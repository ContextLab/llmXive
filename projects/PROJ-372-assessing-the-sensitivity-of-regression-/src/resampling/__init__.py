"""
Resampling module for subset generation and stability estimation.

This module provides functionality to generate random observation subsets
across multiple sample size tiers, fit OLS models, and compute empirical
standard deviations of regression coefficients.

Key components:
- Subset generation with configurable tiers
- Robust OLS fitting with singularity handling
- Coefficient stability analysis
"""

from .engine import (
    generate_subsets,
    fit_ols_models,
    compute_coefficient_stability,
    run_resampling_experiment,
)
from .config import (
    get_sample_size_tiers,
    validate_subset_size,
    load_resampling_config,
)

__all__ = [
    "generate_subsets",
    "fit_ols_models",
    "compute_coefficient_stability",
    "run_resampling_experiment",
    "get_sample_size_tiers",
    "validate_subset_size",
    "load_resampling_config",
]