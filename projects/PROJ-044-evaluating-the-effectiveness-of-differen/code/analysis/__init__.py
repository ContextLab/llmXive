"""
Analysis module for DP-FL evaluation pipeline.

This module contains utilities for statistical analysis, plotting,
and data filtering.
"""

from .stats import (
    filter_time_limited,
    load_metrics_from_csv,
    calculate_rounds_to_target,
    calculate_summary_statistics,
    run_paired_ttest_dp_vs_nondp,
    run_unpaired_ttest_majority_vs_minority,
    generate_validation_report,
    calculate_summary_statistics_for_task,
    run_experiment_analysis
)

from .plots import (
    plot_accuracy_gap_vs_alpha,
    plot_accuracy_vs_epsilon,
    plot_minority_degradation_overlay,
    generate_all_plots
)

from .filters import (
    filter_utility_collapse,
    run_filter_pipeline
)

__all__ = [
    # Stats
    'filter_time_limited',
    'load_metrics_from_csv',
    'calculate_rounds_to_target',
    'calculate_summary_statistics',
    'run_paired_ttest_dp_vs_nondp',
    'run_unpaired_ttest_majority_vs_minority',
    'generate_validation_report',
    'calculate_summary_statistics_for_task',
    'run_experiment_analysis',
    # Plots
    'plot_accuracy_gap_vs_alpha',
    'plot_accuracy_vs_epsilon',
    'plot_minority_degradation_overlay',
    'generate_all_plots',
    # Filters
    'filter_utility_collapse',
    'run_filter_pipeline'
]