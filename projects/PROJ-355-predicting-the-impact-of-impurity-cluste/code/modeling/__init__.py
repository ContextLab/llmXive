"""
Modeling and analysis modules for impurity clustering research.

This package provides utilities for:
- Training regression models on segregation data.
- Performing cross-validation and metric calculation.
- Conducting hypothesis testing and sensitivity analysis.
"""
from .train import train_linear_regression, perform_cross_validation
from .evaluate import evaluate_model, calculate_confidence_intervals
from .hypothesis import test_significance, apply_bonferroni_correction

__all__ = [
    "train_linear_regression",
    "perform_cross_validation",
    "evaluate_model",
    "calculate_confidence_intervals",
    "test_significance",
    "apply_bonferroni_correction",
]