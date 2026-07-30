"""
Analysis package for the Consciousness Bootstrapping project.
Contains statistical tests, report generation, and sensitivity analysis.
"""
from .stats import (
    StatisticalTestResult, StatisticalReport,
    load_evaluation_results_from_json, filter_converged_seeds,
    calculate_percentage_difference, run_paired_ttest, calculate_cohen_d,
    calculate_confidence_interval, bonferroni_correction,
    generate_statistical_report, save_statistical_report,
    run_sensitivity_analysis, main
)
