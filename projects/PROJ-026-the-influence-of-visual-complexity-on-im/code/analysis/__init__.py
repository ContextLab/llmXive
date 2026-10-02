"""
Statistical analysis modules.
"""
from .pca import run_pca_check, main as pca_main
from .permutation import run_permutation_test, calculate_effect_size, save_permutation_results, main as permutation_main
from .results import save_json_results, aggregate_permutation_results, calculate_partial_eta2, run_and_save_all_results, main as results_main
from .sensitivity import load_complexity_scores, load_aggregated_d_scores, re_categorize_complexity, join_with_d_scores, run_analysis_for_threshold, run_loio_analysis, run_sensitivity_analysis, main as sensitivity_main

__all__ = [
    "run_pca_check",
    "pca_main",
    "run_permutation_test",
    "calculate_effect_size",
    "save_permutation_results",
    "permutation_main",
    "save_json_results",
    "aggregate_permutation_results",
    "calculate_partial_eta2",
    "run_and_save_all_results",
    "results_main",
    "load_complexity_scores",
    "load_aggregated_d_scores",
    "re_categorize_complexity",
    "join_with_d_scores",
    "run_analysis_for_threshold",
    "run_loio_analysis",
    "run_sensitivity_analysis",
    "sensitivity_main"
]
