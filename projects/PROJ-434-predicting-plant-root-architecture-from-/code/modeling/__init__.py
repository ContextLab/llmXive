"""
Modeling module for the plant root architecture prediction pipeline.

This module handles:
- Model training and validation
- Feature importance calculation
- Sensitivity analysis
- Metrics generation and reporting
"""

from .train import (
    preprocess_data,
    train_model,
    run_stratified_cv,
    run_loso_cv,
    run_nested_permutation_tests,
    enforce_sc002,
    calculate_p_value,
    main as train_main,
)
from .feature_importance import (
    load_trained_models,
    extract_feature_importance,
    save_feature_importance_csv,
    plot_feature_importance,
    main as feature_importance_main,
)
from .sensitivity import (
    load_feature_importance_data,
    analyze_threshold_sensitivity,
    generate_sensitivity_report,
    main as sensitivity_main,
)
from .generate_metrics import (
    load_model_metrics_from_training_log,
    generate_model_metrics_json,
    main as metrics_main,
)

__all__ = [
    # Training
    "preprocess_data",
    "train_model",
    "run_stratified_cv",
    "run_loso_cv",
    "run_nested_permutation_tests",
    "enforce_sc002",
    "calculate_p_value",
    "train_main",
    # Feature Importance
    "load_trained_models",
    "extract_feature_importance",
    "save_feature_importance_csv",
    "plot_feature_importance",
    "feature_importance_main",
    # Sensitivity
    "load_feature_importance_data",
    "analyze_threshold_sensitivity",
    "generate_sensitivity_report",
    "sensitivity_main",
    # Metrics
    "load_model_metrics_from_training_log",
    "generate_model_metrics_json",
    "metrics_main",
]
