# Analysis module initialization
"""
Analysis module for processing meta-analysis estimation results.

This module exposes the core classes and functions for statistical analysis,
including metrics calculation, statistical tests, and result aggregation.
"""

from .metrics import (
    calculate_bias,
    calculate_coverage,
    calculate_i_squared,
    aggregate_metrics
)

from .stats import (
    exact_binomial_test,
    shapiro_wilk_test,
    bonferroni_correction,
    conditional_statistical_test,
    apply_anova,
    apply_kruskal_wallis
)

__all__ = [
    "calculate_bias",
    "calculate_coverage",
    "calculate_i_squared",
    "aggregate_metrics",
    "exact_binomial_test",
    "shapiro_wilk_test",
    "bonferroni_correction",
    "conditional_statistical_test",
    "apply_anova",
    "apply_kruskal_wallis"
]

# Import logger if needed for module-level logging
try:
    from utils.logging import get_logger
    logger = get_logger(__name__)
except ImportError:
    # Fallback if utils not yet available during initial setup
    import logging
    logger = logging.getLogger(__name__)