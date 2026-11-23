# Evaluation package
"""
Evaluation modules for benchmarking sparse attention heuristics.
Includes metrics, statistical tests, baseline runners, and report generation.
"""

from .metrics import (
    normalize_text,
    calculate_exact_match,
    calculate_f1,
    calculate_perplexity,
    evaluate_predictions,
    calculate_metrics,
)
from .statistical import (
    run_paired_ttest,
    run_wilcoxon_test,
    apply_holm_bonferroni,
    run_sensitivity_sweep,
    calculate_false_positive_rate,
    generate_statistical_report,
)
from .baseline_runner import DenseAttentionRunner, run_baseline_experiment
from .aggregator import load_experiment_results, aggregate_benchmark_report, save_report
from .report_generator import generate_final_report, run_aggregation
from .report_verifier import verify_report
from .exclusion_logger import validate_needle_presence, log_exclusion

__all__ = [
    "normalize_text",
    "calculate_exact_match",
    "calculate_f1",
    "calculate_perplexity",
    "evaluate_predictions",
    "calculate_metrics",
    "run_paired_ttest",
    "run_wilcoxon_test",
    "apply_holm_bonferroni",
    "run_sensitivity_sweep",
    "calculate_false_positive_rate",
    "generate_statistical_report",
    "DenseAttentionRunner",
    "run_baseline_experiment",
    "load_experiment_results",
    "aggregate_benchmark_report",
    "save_report",
    "generate_final_report",
    "run_aggregation",
    "verify_report",
    "validate_needle_presence",
    "log_exclusion",
]
