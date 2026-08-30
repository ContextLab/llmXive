"""
Statistical analysis and reporting.

Exports:
  - StatisticalTestResult, StatisticalReport
  - load_evaluation_results_from_json, filter_converged_seeds
  - calculate_percentage_difference, run_paired_ttest
  - calculate_cohen_d, calculate_confidence_interval
  - bonferroni_correction, generate_statistical_report, save_statistical_report
  - run_sensitivity_analysis
  - apply_patch (from plan_applier), scan_file (from plan_scanner)
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
    run_sensitivity_analysis
)
from .plan_applier import apply_patch
from .plan_scanner import scan_file
