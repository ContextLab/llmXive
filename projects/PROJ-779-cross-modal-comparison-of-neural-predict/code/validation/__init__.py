"""
Validation module for cross-modal comparison of neural prediction error signals.

This module contains functions for reliability analysis and data validation.
"""

from .reliability import (
    ReliabilityError,
    split_half_reliability,
    cronbachs_alpha,
    compute_reliability_metrics,
    save_reliability_results,
    main as reliability_main
)

__all__ = [
    'ReliabilityError',
    'split_half_reliability',
    'cronbachs_alpha',
    'compute_reliability_metrics',
    'save_reliability_results',
    'reliability_main'
]