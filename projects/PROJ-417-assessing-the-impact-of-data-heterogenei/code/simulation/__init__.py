"""
Simulation package initialization.

This file makes the `code.simulation` directory a proper Python package,
allowing imports such as `from code.simulation.estimators import ...`.

The estimators module provides Fixed‑Effects, DerSimonian‑Laird, and REML
meta‑analysis estimators, along with Q and I² calculations, small‑study
flagging, and REML convergence‑failure logging as required by FR‑002,
FR‑006, and Constitution Principle VII.
"""
# Export primary public symbols for convenience
from .estimators import (
    EstimationResult,
    estimate_fixed_effects,
    estimate_dersimonian_laird,
    estimate_reml,
    apply_estimator,
    calculate_i_squared,
    log_reml_failure,
    REML_FAILURE_LOG_PATH,
)

__all__ = [
    "EstimationResult",
    "estimate_fixed_effects",
    "estimate_dersimonian_laird",
    "estimate_reml",
    "apply_estimator",
    "calculate_i_squared",
    "log_reml_failure",
    "REML_FAILURE_LOG_PATH",
]