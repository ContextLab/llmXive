"""
Statistical analysis and permutation testing module for PROJ-026.
"""
from .pca import run_pca_check, main as run_pca_main
from .permutation import (
    run_permutation_test,
    calculate_effect_size,
    run_post_hoc_power_analysis,
    run_sensitivity_analysis,
    run_loio_analysis,
)
from .results import save_json_results, aggregate_permutation_results, run_and_save_all_results
from .sensitivity import (
    load_complexity_scores,
    load_aggregated_d_scores,
    re_categorize_complexity,
    join_with_d_scores,
    run_analysis_for_threshold,
)

__all__ = [
    "run_pca_check",
    "run_pca_main",
    "run_permutation_test",
    "calculate_effect_size",
    "run_post_hoc_power_analysis",
    "run_sensitivity_analysis",
    "run_loio_analysis",
    "save_json_results",
    "aggregate_permutation_results",
    "run_and_save_all_results",
    "load_complexity_scores",
    "load_aggregated_d_scores",
    "re_categorize_complexity",
    "join_with_d_scores",
    "run_analysis_for_threshold",
]
