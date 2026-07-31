"""
Analysis module for texture evolution validation and physics checks.
"""

from .texture_validation import (
    validate_sample_trends,
    validate_dataset_trends,
    flag_deviant_samples,
    calculate_expected_trend,
    calculate_trend_deviation,
    aggregate_deviation_score
)

__all__ = [
    'validate_sample_trends',
    'validate_dataset_trends',
    'flag_deviant_samples',
    'calculate_expected_trend',
    'calculate_trend_deviation',
    'aggregate_deviation_score'
]