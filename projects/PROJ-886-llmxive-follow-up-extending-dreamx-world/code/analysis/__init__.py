"""
Analysis module for DreamX-Lite metrics and statistical evaluation.
"""
from .metrics_writer import write_metrics_csv, load_metrics_csv, main
from .sensitivity import compute_success_rate_at_threshold, run_sensitivity_analysis
from .stats import (
    load_convergence_flags,
    calculate_censoring_rate,
    mcnemar_test,
    wilcoxon_signed_rank_test,
    calculate_information_theoretic_sufficiency_ratio
)

__all__ = [
    'write_metrics_csv',
    'load_metrics_csv',
    'main',
    'compute_success_rate_at_threshold',
    'run_sensitivity_analysis',
    'load_convergence_flags',
    'calculate_censoring_rate',
    'mcnemar_test',
    'wilcoxon_signed_rank_test',
    'calculate_information_theoretic_sufficiency_ratio'
]
