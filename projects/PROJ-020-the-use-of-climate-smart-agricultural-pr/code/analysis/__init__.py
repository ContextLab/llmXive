"""Analysis package for statistical modeling and diagnostics."""

from .model import (
    run_mixed_effects_model,
    calculate_fdr_adjusted_pvalues,
    run_mediation_analysis,
    run_robustness_checks,
    main
)
from .diagnostics import (
    calculate_vif,
    flag_collinearity,
    get_collinearity_report
)
from .robustness import (
    run_bootstrap_resampling,
    run_leave_one_region_out,
    run_robustness_pipeline,
    main
)
from .performance import (
    run_batched_model_fitting,
    run_optimized_model_pipeline,
    optimize_dataframe_for_modeling,
    create_batches,
    estimate_dataframe_memory,
    get_available_memory
)

__all__ = [
    'run_mixed_effects_model',
    'calculate_fdr_adjusted_pvalues',
    'run_mediation_analysis',
    'run_robustness_checks',
    'main',
    'calculate_vif',
    'flag_collinearity',
    'get_collinearity_report',
    'run_bootstrap_resampling',
    'run_leave_one_region_out',
    'run_robustness_pipeline',
    'run_batched_model_fitting',
    'run_optimized_model_pipeline',
    'optimize_dataframe_for_modeling',
    'create_batches',
    'estimate_dataframe_memory',
    'get_available_memory'
]