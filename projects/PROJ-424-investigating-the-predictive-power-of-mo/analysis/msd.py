"""
Wrapper module exposing the MSD utilities under the top‑level ``analysis``
namespace.  All public symbols are re‑exported from ``code.analysis.msd``.
"""

from code.analysis.msd import (
    load_trajectory_timeseries,
    perform_linear_regression,
    validate_linearity,
    calculate_diffusion_coefficient,
    main,
)

__all__ = [
    "load_trajectory_timeseries",
    "perform_linear_regression",
    "validate_linearity",
    "calculate_diffusion_coefficient",
    "main",
]
