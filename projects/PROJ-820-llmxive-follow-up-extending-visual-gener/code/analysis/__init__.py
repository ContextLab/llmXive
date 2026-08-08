"""
Analysis module for llmXive follow-up project.
Contains modules for contradiction analysis and statistical evaluation.
"""
from .contradiction_analyzer import (
    StudyFlagError,
    load_contradiction_log,
    calculate_contradiction_rate,
    verify_contradiction_rate,
    flag_study_if_high_rate,
    run_contradiction_analysis,
    main as contradiction_main
)
from .statistics import (
    StudyInvalidError,
    calculate_effect_size,
    power_analysis_two_proportions,
    two_proportion_z_test,
    fisher_exact_test,
    select_statistical_test,
    load_evaluation_results,
    aggregate_violation_rates,
    calculate_contradiction_rate as stats_contradiction_rate,
    verify_contradiction_rate as stats_verify_rate,
    run_power_analysis_and_report,
    run_statistical_comparison,
    generate_final_analysis_csv,
    main as stats_main
)

__all__ = [
    # Contradiction Analyzer exports
    'StudyFlagError',
    'load_contradiction_log',
    'calculate_contradiction_rate',
    'verify_contradiction_rate',
    'flag_study_if_high_rate',
    'run_contradiction_analysis',
    'contradiction_main',
    # Statistics exports
    'StudyInvalidError',
    'calculate_effect_size',
    'power_analysis_two_proportions',
    'two_proportion_z_test',
    'fisher_exact_test',
    'select_statistical_test',
    'load_evaluation_results',
    'aggregate_violation_rates',
    'calculate_contradiction_rate',
    'verify_contradiction_rate',
    'run_power_analysis_and_report',
    'run_statistical_comparison',
    'generate_final_analysis_csv',
    'stats_main'
]
