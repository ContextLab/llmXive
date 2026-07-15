"""
Configuration module for Bloom Filter benchmarks.
Provides constants and helper functions for FPR targets and parameter calculation.
"""
from typing import List, Dict
from .base import calculate_optimal_parameters, get_config_for_sizes, FPR_TARGETS


# Re-export for convenience
__all__ = [
    "FPR_TARGETS",
    "calculate_optimal_parameters",
    "get_config_for_sizes"
]