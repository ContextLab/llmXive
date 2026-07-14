"""
Models module for fitting, evaluating, and saving statistical models.
"""
from src.models.fit import fit_gaussian_glm, fit_ridge_regression, prepare_features_for_model, collapse_eco_to_family
from src.models.metrics import (
    calculate_wald_z_test,
    calculate_f_statistic,
    calculate_model_f_statistic,
    apply_benjamini_hochberg_fdr,
    extract_metrics_from_statsmodels_result,
    calculate_feature_significance
)
from src.models.save_metrics import save_model_metrics, save_single_model_metrics

__all__ = [
    "fit_gaussian_glm",
    "fit_ridge_regression",
    "prepare_features_for_model",
    "collapse_eco_to_family",
    "calculate_wald_z_test",
    "calculate_f_statistic",
    "calculate_model_f_statistic",
    "apply_benjamini_hochberg_fdr",
    "extract_metrics_from_statsmodels_result",
    "calculate_feature_significance",
    "save_model_metrics",
    "save_single_model_metrics"
]
