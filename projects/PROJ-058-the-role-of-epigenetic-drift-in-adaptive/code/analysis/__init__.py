"""
Analysis module for correlation and statistical testing.
"""

from correlation import (
    load_variance_matrix,
    filter_by_condition,
    calculate_spearman_correlation,
    run_iterative_permutation_test,
    run_correlation_analysis,
    save_results,
    main
)

from timescale_align import (
    load_timescale_data,
    extract_env_timescale,
    calculate_drift_timescale,
    calculate_alignment_status,
    process_timescale_alignment,
    save_results,
    run_timescale_alignment,
    main
)

from sensitivity import (
    load_correlation_results,
    filter_by_generation_threshold,
    run_sensitivity_sweep,
    save_results,
    run_sensitivity_analysis,
    main
)

from stability_check import (
    load_sensitivity_results,
    check_significance_count,
    calculate_max_rho_diff,
    perform_stability_check,
    save_results,
    run_stability_analysis,
    main
)

from stressor_stratification import (
    load_metadata_from_variance_matrix,
    get_stressor_column,
    get_env_type_column,
    stratify_by_stressor,
    run_stressor_stratification,
    main
)

__all__ = [
    # Correlation
    "load_variance_matrix",
    "filter_by_condition",
    "calculate_spearman_correlation",
    "run_iterative_permutation_test",
    "run_correlation_analysis",
    "save_results",
    # Timescale alignment
    "load_timescale_data",
    "extract_env_timescale",
    "calculate_drift_timescale",
    "calculate_alignment_status",
    "process_timescale_alignment",
    "run_timescale_alignment",
    # Sensitivity
    "load_correlation_results",
    "filter_by_generation_threshold",
    "run_sensitivity_sweep",
    "run_sensitivity_analysis",
    # Stability
    "load_sensitivity_results",
    "check_significance_count",
    "calculate_max_rho_diff",
    "perform_stability_check",
    # Stressor stratification
    "load_metadata_from_variance_matrix",
    "get_stressor_column",
    "get_env_type_column",
    "stratify_by_stressor",
    "run_stressor_stratification"
]
