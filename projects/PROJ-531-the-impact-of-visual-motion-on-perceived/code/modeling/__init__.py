"""
Statistical modeling and analysis modules.
"""
from .model_fitting import fit_ols, fit_ridge, fit_random_forest, main as model_fitting_main
from .stats_utils import bonferroni_correction, benjamini_hochberg_correction
from .sensitivity_analysis import bootstrap_sensitivity_check, run_sensitivity_analysis, main as sensitivity_main
from .compute_metrics import compute_out_of_sample_metrics, extract_feature_importance, run_metric_computation
from .generate_metrics_json import load_cleaned_data, run_metric_aggregation, main as metrics_json_main
from .add_correlational_framing import add_correlational_framing, main as framing_main

__all__ = [
    "fit_ols",
    "fit_ridge",
    "fit_random_forest",
    "model_fitting_main",
    "bonferroni_correction",
    "benjamini_hochberg_correction",
    "bootstrap_sensitivity_check",
    "run_sensitivity_analysis",
    "sensitivity_main",
    "compute_out_of_sample_metrics",
    "extract_feature_importance",
    "run_metric_computation",
    "load_cleaned_data",
    "run_metric_aggregation",
    "metrics_json_main",
    "add_correlational_framing",
    "framing_main",
]
