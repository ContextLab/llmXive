"""
Analysis package for the Robustness of Confidence Intervals project.
"""

from .ci_builder import (
    bootstrap_resample,
    compute_percentile_ci,
    build_ci_for_mean,
    build_ci_for_regression_coefficient,
    build_ci_for_variance,
    validate_ci_coverage
)
from .dp_noise import (
    compute_laplace_scale,
    compute_gaussian_scale,
    inject_laplace_noise,
    inject_gaussian_noise,
    apply_dp_to_summary,
    validate_dp_parameters
)
from .edge_cases import (
    clamp_noise_scale,
    detect_collinearity,
    enforce_minimum_sample_size,
    validate_covariance_matrix,
    handle_zero_variance
)
from .adjustments import (
    apply_bias_correction_mean,
    apply_variance_inflation_regression,
    apply_adjustments_to_summary,
    compute_adjusted_ci
)
from .glm_analysis import fit_coverage_glm
from .plotting import (
    load_coverage_data,
    aggregate_coverage_stats,
    plot_coverage_vs_epsilon
)
from .convergence_check import (
    calculate_coverage_se,
    check_convergence,
    main as check_convergence_main
)

__all__ = [
    'bootstrap_resample', 'compute_percentile_ci', 'build_ci_for_mean',
    'build_ci_for_regression_coefficient', 'build_ci_for_variance',
    'validate_ci_coverage',
    'compute_laplace_scale', 'compute_gaussian_scale', 'inject_laplace_noise',
    'inject_gaussian_noise', 'apply_dp_to_summary', 'validate_dp_parameters',
    'clamp_noise_scale', 'detect_collinearity', 'enforce_minimum_sample_size',
    'validate_covariance_matrix', 'handle_zero_variance',
    'apply_bias_correction_mean', 'apply_variance_inflation_regression',
    'apply_adjustments_to_summary', 'compute_adjusted_ci',
    'fit_coverage_glm',
    'load_coverage_data', 'aggregate_coverage_stats', 'plot_coverage_vs_epsilon',
    'calculate_coverage_se', 'check_convergence', 'check_convergence_main'
]
