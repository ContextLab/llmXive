"""
Statistical analysis and plan management.
Exports: Stats functions, Plan scanner/applier
"""
from .stats import (
    StatisticalTestResult,
    StatisticalReport,
    load_evaluation_results_from_json,
    filter_converged_seeds,
    calculate_percentage_difference,
    run_paired_ttest,
    calculate_cohen_d,
    calculate_confidence_interval,
    bonferroni_correction,
    generate_statistical_report,
    save_statistical_report,
    run_sensitivity_analysis,
    main
)
from .plan_scanner import scan_file, main as scan_main
from .plan_applier import apply_patch, main as apply_main

__all__ = [
    "StatisticalTestResult",
    "StatisticalReport",
    "load_evaluation_results_from_json",
    "filter_converged_seeds",
    "calculate_percentage_difference",
    "run_paired_ttest",
    "calculate_cohen_d",
    "calculate_confidence_interval",
    "bonferroni_correction",
    "generate_statistical_report",
    "save_statistical_report",
    "run_sensitivity_analysis",
    "main",
    "scan_file",
    "scan_main",
    "apply_patch",
    "apply_main"
]
