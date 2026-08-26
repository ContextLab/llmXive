"""
code.analysis package.

This package contains modules for statistical analysis, generalization testing,
and metrics computation for the DOPD research pipeline.
"""

from .stats import (
    mann_whitney_u_test,
    calculate_effect_size,
    calculate_coefficient_of_variation,
    compare_convergence_steps,
)
from .generalization_test import (
    evaluate_masked_performance,
    calculate_performance_drop,
)

__all__ = [
    "mann_whitney_u_test",
    "calculate_effect_size",
    "calculate_coefficient_of_variation",
    "compare_convergence_steps",
    "evaluate_masked_performance",
    "calculate_performance_drop",
]