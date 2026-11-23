# evaluation package
"""
Package for model evaluation, statistical analysis, and reporting.
Includes error metrics, ANOVA/Tukey HSD tests, and generalization analysis.
"""
from .stats_utils import compute_one_way_anova, compute_tukey_hsd, compute_degradation_rate, main as stats_main
from .evaluate import load_predictions, load_ground_truth, compute_errors, generate_report, main as eval_main

__all__ = [
    "compute_one_way_anova",
    "compute_tukey_hsd",
    "compute_degradation_rate",
    "load_predictions",
    "load_ground_truth",
    "compute_errors",
    "generate_report",
]
