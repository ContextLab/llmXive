"""
llmXive Utilities Package.

This package provides shared utilities for the plant root architecture prediction pipeline,
including geocoding, statistics, exception handling, logging, and configuration management.
"""

from .exceptions import DataQualityError, GeocodingError, SpeciesFilterError
from .geocoding import (
    validate_coordinates,
    align_crs,
    transform_coordinates,
    get_central_meridian,
    is_valid_crs,
    get_utm_zone,
    get_utm_crs,
)
from .stats import (
    calculate_metrics,
    calculate_baseline_r2,
    delta_r2,
    permutation_test,
    stratified_permutation_test,
)
from .config import Config, load_environment, get_env, get_config
from .logging_utils import (
    setup_logging,
    get_logger,
    log_excluded_record,
    log_species_exclusion_summary,
    log_validation_failure,
)

__all__ = [
    # Exceptions
    "DataQualityError",
    "GeocodingError",
    "SpeciesFilterError",
    # Geocoding
    "validate_coordinates",
    "align_crs",
    "transform_coordinates",
    "get_central_meridian",
    "is_valid_crs",
    "get_utm_zone",
    "get_utm_crs",
    # Statistics
    "calculate_metrics",
    "calculate_baseline_r2",
    "delta_r2",
    "permutation_test",
    "stratified_permutation_test",
    # Configuration
    "Config",
    "load_environment",
    "get_env",
    "get_config",
    # Logging
    "setup_logging",
    "get_logger",
    "log_excluded_record",
    "log_species_exclusion_summary",
    "log_validation_failure",
]