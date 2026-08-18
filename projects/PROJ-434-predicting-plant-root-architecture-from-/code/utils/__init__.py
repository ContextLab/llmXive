"""
llmXive Utilities Package

This package contains shared utilities for data processing, geocoding,
statistics, and exception handling used across the pipeline.
"""

from .exceptions import DataQualityError, GeocodingError, SpeciesFilterError
from .geocoding import validate_coordinates, align_crs, get_central_meridian
from .stats import (
    calculate_metrics,
    calculate_baseline_r2,
    delta_r2,
    permutation_test,
    stratified_permutation_test
)
from .config import Config, load_environment, get_env

__all__ = [
    # Exceptions
    'DataQualityError',
    'GeocodingError',
    'SpeciesFilterError',
    # Geocoding
    'validate_coordinates',
    'align_crs',
    'get_central_meridian',
    # Statistics
    'calculate_metrics',
    'calculate_baseline_r2',
    'delta_r2',
    'permutation_test',
    'stratified_permutation_test',
    # Config
    'Config',
    'load_environment',
    'get_env'
]

__version__ = "0.1.0"