"""
Evaluation module for cross-validation, bootstrap, and model comparison.
"""
from .cv import run_kfold_cv, run_cross_validation_for_all_models, main as cv_main
from .bootstrap import bootstrap_metrics, BootstrapEvaluator, main as bootstrap_main
from .model_comparison import generate_comparison_report, main as comparison_main
from .sensitivity import run_sensitivity_analysis, main as sensitivity_main
from .shap_analysis import SHAPAnalyzer, main as shap_main

__all__ = [
    "run_kfold_cv",
    "bootstrap_metrics",
    "generate_comparison_report",
    "run_sensitivity_analysis",
    "SHAPAnalyzer"
]
