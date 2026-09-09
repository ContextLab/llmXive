"""
Analysis package initialization.
Exports public API for analysis modules including boundedness checks.
"""
from .boundedness import (
    BoundednessCheckResult,
    check_trajectory_boundedness,
    run_boundedness_validation_batch,
    save_validation_report,
    main as boundedness_main
)

from .baseline import (
    NonChaoticSystemError,
    BaselineConvergenceError,
    BaselineResult,
    compute_asymptotic_baseline,
    validate_clean_system_baseline,
    save_baseline_result,
    load_baseline_result,
    validate_and_gate_for_baseline
)

from .ftle import (
    FTLEResult,
    compute_jacobian,
    propagate_tangent_vectors,
    orthonormalize,
    compute_ftle_single_trajectory,
    run_sliding_window_sweep,
    compute_ftle_batch,
    load_baseline_and_compute_ftle,
    save_ftle_results,
    main as ftle_main
)

from .regression import (
    RegressionResult,
    TrialValidationReport,
    validate_trial_counts,
    load_ftle_sweep_results,
    load_baseline_results,
    compute_deviations,
    run_ttest_bias,
    select_best_model,
    calculate_scaling_exponent,
    generate_deviation_plot,
    generate_convergence_plot,
    run_full_regression_analysis,
    main as regression_main
)

__all__ = [
    # Boundedness (T043)
    'BoundednessCheckResult',
    'check_trajectory_boundedness',
    'run_boundedness_validation_batch',
    'save_validation_report',
    'boundedness_main',
    
    # Baseline
    'NonChaoticSystemError',
    'BaselineConvergenceError',
    'BaselineResult',
    'compute_asymptotic_baseline',
    'validate_clean_system_baseline',
    'save_baseline_result',
    'load_baseline_result',
    'validate_and_gate_for_baseline',
    
    # FTLE
    'FTLEResult',
    'compute_jacobian',
    'propagate_tangent_vectors',
    'orthonormalize',
    'compute_ftle_single_trajectory',
    'run_sliding_window_sweep',
    'compute_ftle_batch',
    'load_baseline_and_compute_ftle',
    'save_ftle_results',
    'ftle_main',
    
    # Regression
    'RegressionResult',
    'TrialValidationReport',
    'validate_trial_counts',
    'load_ftle_sweep_results',
    'load_baseline_results',
    'compute_deviations',
    'run_ttest_bias',
    'select_best_model',
    'calculate_scaling_exponent',
    'generate_deviation_plot',
    'generate_convergence_plot',
    'run_full_regression_analysis',
    'regression_main'
]