"""
Analysis module for the Consciousness Bootstrapping project.
Contains utilities for scanning, patching, and statistical analysis.
"""
from .plan_scanner import scan_file, main
from .plan_applier import apply_patch, main as apply_main
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
    main as stats_main
)

__all__ = [
    "scan_file",
    "main",
    "apply_patch",
    "apply_main",
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
    "stats_main"
]