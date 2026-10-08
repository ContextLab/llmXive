"""
Analysis module for llmXive.
Contains statistical analysis and contradiction checking logic.
"""

from .contradiction_analyzer import (
    StudyFlagError,
    load_contradiction_log,
    calculate_contradiction_rate,
    verify_contradiction_rate,
    flag_study_if_high_rate,
    run_contradiction_analysis,
    main
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
    calculate_contradiction_rate,
    verify_contradiction_rate,
    run_power_analysis_and_report,
    run_statistical_comparison,
    generate_final_analysis_csv,
    main as stats_main
)

__all__ = [
    # Contradiction Analyzer
    'StudyFlagError',
    'load_contradiction_log',
    'calculate_contradiction_rate',
    'verify_contradiction_rate',
    'flag_study_if_high_rate',
    'run_contradiction_analysis',
    'main',
    
    # Statistics
    'StudyInvalidError',
    'calculate_effect_size',
    'power_analysis_two_proportions',
    'two_proportion_z_test',
    'fisher_exact_test',
    'select_statistical_test',
    'load_evaluation_results',
    'aggregate_violation_rates',
    'run_power_analysis_and_report',
    'run_statistical_comparison',
    'generate_final_analysis_csv',
    'stats_main'
]
