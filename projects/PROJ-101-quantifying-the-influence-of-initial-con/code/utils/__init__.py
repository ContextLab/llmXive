"""
Utilities package for numerical stability and other helper functions.
"""
from .stability import (
    NumericalStabilityError,
    DivergenceError,
    NonConvergenceError,
    StabilityReport,
    check_numerical_validity,
    check_boundedness,
    check_convergence,
    validate_trajectory,
    detect_divergence_rate
)

__all__ = [
    'NumericalStabilityError',
    'DivergenceError',
    'NonConvergenceError',
    'StabilityReport',
    'check_numerical_validity',
    'check_boundedness',
    'check_convergence',
    'validate_trajectory',
    'detect_divergence_rate'
]