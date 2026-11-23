"""
Analysis module for the Social Support Resilience pipeline.

This module contains all statistical analysis, modeling, and results generation code.
"""

from .bootstrap_ci import load_seed_config, compute_bca_bootstrap_ci, run_bootstrap_analysis, main
from .fdr_correction import load_regression_results, apply_benjamini_hochberg, add_fdr_correction_to_results, main as fdr_main
from .models import load_synthetic_cohort, create_interaction_term, fit_ols_model, extract_model_results, estimate_bootstrap_runtime, run_all_models, main as models_main
from .performance_benchmark import run_benchmark, main as benchmark_main
from .results import load_analysis_cohort, load_regression_results, generate_summary_stats, format_coefficient, generate_markdown_report, save_report, main as results_main
from .scales import load_scale_config, score_cesd, score_gad7, score_pcl5, apply_scale_scoring, main as scales_main
from .sensitivity import load_baseline_results, fit_ols_model_continuous, stratify_by_platform, run_sensitivity_analysis, save_results, main as sensitivity_main
from .sensitivity_compare import load_baseline_results, load_sensitivity_results, extract_interaction_coefficients, compare_coefficients, save_comparison_table, run_sensitivity_comparison, main as sensitivity_compare_main
from .validation import load_analysis_cohort, check_harassment_variance, check_vif, validate_analysis_cohort, main as validation_main
from .save_cohort import save_validated_cohort, main as save_cohort_main
from .save_regression_results import load_regression_results_from_memory, load_bootstrap_cis, merge_results, apply_fdr_and_save, main as save_regression_main
from .save_sensitivity_results import main as save_sensitivity_main
from .run_sensitivity_comparison import main as run_sensitivity_comparison_main

__all__ = [
    'load_seed_config', 'compute_bca_bootstrap_ci', 'run_bootstrap_analysis', 'main',
    'load_regression_results', 'apply_benjamini_hochberg', 'add_fdr_correction_to_results', 'fdr_main',
    'load_synthetic_cohort', 'create_interaction_term', 'fit_ols_model', 'extract_model_results', 'estimate_bootstrap_runtime', 'run_all_models', 'models_main',
    'run_benchmark', 'benchmark_main',
    'load_analysis_cohort', 'generate_summary_stats', 'format_coefficient', 'generate_markdown_report', 'save_report', 'results_main',
    'load_scale_config', 'score_cesd', 'score_gad7', 'score_pcl5', 'apply_scale_scoring', 'scales_main',
    'fit_ols_model_continuous', 'stratify_by_platform', 'run_sensitivity_analysis', 'save_results', 'sensitivity_main',
    'load_baseline_results', 'load_sensitivity_results', 'extract_interaction_coefficients', 'compare_coefficients', 'save_comparison_table', 'run_sensitivity_comparison', 'sensitivity_compare_main',
    'check_harassment_variance', 'check_vif', 'validate_analysis_cohort', 'validation_main',
    'save_validated_cohort', 'save_cohort_main',
    'load_regression_results_from_memory', 'load_bootstrap_cis', 'merge_results', 'apply_fdr_and_save', 'save_regression_main',
    'save_sensitivity_main',
    'run_sensitivity_comparison_main'
]
