"""
Modeling package for training and evaluation.
"""
from .train import preprocess_data, train_model, run_loso_cv, run_stratified_cv, run_nested_permutation_tests, calculate_p_value, enforce_sc002, main as train_main
from .baseline import load_merged_data, calculate_mean_baseline_r2, run_loso_baseline_analysis, main as baseline_main
from .feature_importance import load_trained_models, extract_feature_importance, save_feature_importance_csv, plot_feature_importance, main as importance_main
from .generate_metrics import load_model_metrics_from_training_log, generate_model_metrics_json, main as metrics_main
from .sc002_validator import load_permutation_distributions, calculate_p_value, calculate_delta_r2, validate_sc002, main as sc002_main
from .sensitivity import load_feature_importance_data, analyze_threshold_sensitivity, generate_sensitivity_report, main as sensitivity_main

__all__ = [
    "preprocess_data", "train_model", "run_loso_cv", "run_stratified_cv", "run_nested_permutation_tests", "calculate_p_value", "enforce_sc002", "train_main",
    "load_merged_data", "calculate_mean_baseline_r2", "run_loso_baseline_analysis", "baseline_main",
    "load_trained_models", "extract_feature_importance", "save_feature_importance_csv", "plot_feature_importance", "importance_main",
    "load_model_metrics_from_training_log", "generate_model_metrics_json", "metrics_main",
    "load_permutation_distributions", "calculate_p_value", "calculate_delta_r2", "validate_sc002", "sc002_main",
    "load_feature_importance_data", "analyze_threshold_sensitivity", "generate_sensitivity_report", "sensitivity_main"
]
