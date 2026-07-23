"""Statistical modeling, diagnostics, and robustness analysis package."""
from .diagnostics import (
    calculate_vif,
    flag_collinearity,
    get_collinearity_report,
    main as diagnostics_main
)
from .model import (
    log_memory_profile,
    reset_memory_profile,
    calculate_fdr_adjusted_pvalues,
    run_mixed_effects_model,
    run_mediation_analysis,
    run_robustness_checks,
    save_memory_profile_report,
    main as model_main
)
from .robustness import (
    load_model_results,
    run_bootstrap_resampling,
    run_leave_one_region_out,
    run_robustness_pipeline,
    main as robustness_main
)
from .performance import (
    estimate_dataframe_memory,
    downcast_dataframe,
    split_dataframe_by_memory,
    fit_model_batch,
    run_batched_model_fitting,
    calculate_memory_requirements,
    main as performance_main
)

__all__ = [
    'calculate_vif', 'flag_collinearity', 'get_collinearity_report', 'diagnostics_main',
    'log_memory_profile', 'reset_memory_profile', 'calculate_fdr_adjusted_pvalues',
    'run_mixed_effects_model', 'run_mediation_analysis', 'run_robustness_checks',
    'save_memory_profile_report', 'model_main',
    'load_model_results', 'run_bootstrap_resampling', 'run_leave_one_region_out',
    'run_robustness_pipeline', 'robustness_main',
    'estimate_dataframe_memory', 'downcast_dataframe', 'split_dataframe_by_memory',
    'fit_model_batch', 'run_batched_model_fitting', 'calculate_memory_requirements',
    'performance_main'
]
