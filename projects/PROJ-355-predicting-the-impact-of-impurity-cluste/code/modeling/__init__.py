"""
Modeling and analysis modules for impurity clustering research.

This package provides utilities for:
- Training regression models on segregation data.
- Performing cross-validation and metric calculation.
- Conducting hypothesis testing and sensitivity analysis.
"""
from .train import train_model, run_kfold_cv, calculate_confidence_intervals
from .evaluate import run_sensitivity_analysis, calculate_rmse_variance
from .confidence_intervals import calculate_prediction_intervals, run_confidence_interval_analysis
from .sensitivity_metrics import compute_sensitivity_metrics, save_sensitivity_metrics
from .evaluate_per_system import evaluate_per_system, run_per_system_evaluation

__all__ = [
    "train_model",
    "run_kfold_cv",
    "calculate_confidence_intervals",
    "run_sensitivity_analysis",
    "calculate_rmse_variance",
    "calculate_prediction_intervals",
    "run_confidence_interval_analysis",
    "compute_sensitivity_metrics",
    "save_sensitivity_metrics",
    "evaluate_per_system",
    "run_per_system_evaluation",
]