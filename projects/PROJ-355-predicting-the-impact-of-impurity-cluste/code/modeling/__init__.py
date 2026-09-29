# Modeling module
"""
This module contains utilities for model training, evaluation, and analysis, including:
- Training regression models (Linear Regression for MVP)
- Cross-validation procedures
- Metric calculation (R², RMSE, p-values)
- Confidence interval estimation
- Sensitivity analysis
- Per-system evaluation
"""

from .train import (
    load_schema,
    validate_input_data,
    check_collinearity_warning,
    train_model,
    run_kfold_cv,
    calculate_confidence_intervals,
    save_results,
    main as train_main,
)
from .evaluate import (
    load_output_schema,
    validate_model_output,
    validate_output_file,
    run_contract_validation,
    calculate_rmse_variance,
    run_sensitivity_analysis,
    main as evaluate_main,
)
from .evaluate_per_system import (
    load_alloy_systems,
    load_processed_data,
    evaluate_per_system,
    save_per_system_results,
    run_per_system_evaluation,
    main as evaluate_per_system_main,
)
from .confidence_intervals import (
    calculate_prediction_intervals,
    calculate_confidence_intervals_mean,
    add_confidence_intervals_to_results,
    run_confidence_interval_analysis,
)
from .sensitivity_metrics import (
    calculate_rmse_variance as calc_rmse_variance,
    calculate_r2_stability,
    compute_sensitivity_metrics,
    run_sensitivity_metrics_analysis,
    save_sensitivity_metrics,
    main as sensitivity_metrics_main,
)

__all__ = [
    "load_schema",
    "validate_input_data",
    "check_collinearity_warning",
    "train_model",
    "run_kfold_cv",
    "calculate_confidence_intervals",
    "save_results",
    "train_main",
    "load_output_schema",
    "validate_model_output",
    "validate_output_file",
    "run_contract_validation",
    "calculate_rmse_variance",
    "run_sensitivity_analysis",
    "evaluate_main",
    "load_alloy_systems",
    "load_processed_data",
    "evaluate_per_system",
    "save_per_system_results",
    "run_per_system_evaluation",
    "evaluate_per_system_main",
    "calculate_prediction_intervals",
    "calculate_confidence_intervals_mean",
    "add_confidence_intervals_to_results",
    "run_confidence_interval_analysis",
    "calc_rmse_variance",
    "calculate_r2_stability",
    "compute_sensitivity_metrics",
    "run_sensitivity_metrics_analysis",
    "save_sensitivity_metrics",
    "sensitivity_metrics_main",
]