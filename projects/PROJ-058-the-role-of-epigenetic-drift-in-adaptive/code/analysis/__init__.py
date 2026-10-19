"""
Analysis package initialization.

Exposes the public analysis API using explicit relative imports so that
importing ``analysis`` or any of its submodules works regardless of how
the package is placed on ``sys.path``. The previous implementation used
unqualified imports (``from correlation import ...``), which raised
``ModuleNotFoundError`` because ``correlation`` is not a top-level module.
"""

from .correlation import (
    load_variance_matrix,
    filter_by_condition,
    calculate_spearman_correlation,
    run_iterative_permutation_test,
    run_correlation_analysis,
    save_results as save_correlation_results,
)

from .timescale_align import (
    load_timescale_data,
    extract_env_timescale,
    calculate_drift_timescale,
    calculate_alignment_status,
    process_timescale_alignment,
    save_results as save_timescale_results,
    run_timescale_alignment,
)

from .sensitivity import (
    load_correlation_results,
    filter_by_generation_threshold,
    run_sensitivity_sweep,
    save_results as save_sensitivity_results,
    run_sensitivity_analysis,
)

from .stability_check import (
    load_sensitivity_results,
    check_significance_count,
    calculate_max_rho_diff,
    perform_stability_check,
    save_results as save_stability_results,
    run_stability_analysis,
)

from .stressor_stratification import (
    load_metadata_from_variance_matrix,
    get_stressor_column,
    get_env_type_column,
    stratify_by_stressor,
    run_stressor_stratification,
)

__all__ = [
    # Correlation
    "load_variance_matrix",
    "filter_by_condition",
    "calculate_spearman_correlation",
    "run_iterative_permutation_test",
    "run_correlation_analysis",
    "save_correlation_results",
    # Timescale alignment
    "load_timescale_data",
    "extract_env_timescale",
    "calculate_drift_timescale",
    "calculate_alignment_status",
    "process_timescale_alignment",
    "save_timescale_results",
    "run_timescale_alignment",
    # Sensitivity
    "load_correlation_results",
    "filter_by_generation_threshold",
    "run_sensitivity_sweep",
    "save_sensitivity_results",
    "run_sensitivity_analysis",
    # Stability
    "load_sensitivity_results",
    "check_significance_count",
    "calculate_max_rho_diff",
    "perform_stability_check",
    "save_stability_results",
    "run_stability_analysis",
    # Stressor stratification
    "load_metadata_from_variance_matrix",
    "get_stressor_column",
    "get_env_type_column",
    "stratify_by_stressor",
    "run_stressor_stratification",
]
