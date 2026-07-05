"""
Analysis module for estimating meta-analysis metrics.

Exposes core estimators and metric calculation functions.
"""

from .estimators import fixed_effects, dersoninian_laird, reml
from .metrics import calculate_bias, calculate_coverage

__all__ = [
    "fixed_effects",
    "dersoninian_laird",
    "reml",
    "calculate_bias",
    "calculate_coverage",
]