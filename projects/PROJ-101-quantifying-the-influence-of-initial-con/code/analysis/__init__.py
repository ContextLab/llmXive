"""
Analysis module for chaotic system dynamics.
"""

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
from .shadowing import (
    ShadowingResult,
    ShadowingCheckError,
    compute_divergence_rate,
    validate_shadowing_lemma,
    run_shadowing_check_batch,
    gate_for_ftle_calculation
)
from .ftle import (
    FTLEResult,
    compute_jacobian,
    propagate_tangent_vectors,
    orthonormalize,
    compute_ftle_single_trajectory,
    compute_ftle_batch,
    main
)

__all__ = [
    # Baseline
    'NonChaoticSystemError',
    'BaselineConvergenceError',
    'BaselineResult',
    'compute_asymptotic_baseline',
    'validate_clean_system_baseline',
    'save_baseline_result',
    'load_baseline_result',
    'validate_and_gate_for_baseline',
    # Shadowing
    'ShadowingResult',
    'ShadowingCheckError',
    'compute_divergence_rate',
    'validate_shadowing_lemma',
    'run_shadowing_check_batch',
    'gate_for_ftle_calculation',
    # FTLE
    'FTLEResult',
    'compute_jacobian',
    'propagate_tangent_vectors',
    'orthonormalize',
    'compute_ftle_single_trajectory',
    'compute_ftle_batch',
    'main'
]