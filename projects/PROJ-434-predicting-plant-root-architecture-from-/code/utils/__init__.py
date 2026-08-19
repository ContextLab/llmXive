"""
Utilities package for the plant root architecture prediction pipeline.

This package contains shared utilities for:
- Configuration management
- Exception handling
- Geocoding and coordinate transformations
- Logging utilities
- Statistical functions
"""

from .config import Config, load_environment, get_env, get_config
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
from .logging_utils import (
    setup_logging,
    get_logger,
    log_excluded_record,
    log_species_exclusion_summary,
    log_validation_failure,
)
from .stats import (
    calculate_metrics,
    calculate_baseline_r2,
    delta_r2,
    permutation_test,
    stratified_permutation_test,
)

__all__ = [
    # Config
    "Config",
    "load_environment",
    "get_env",
    "get_config",
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
    # Logging
    "setup_logging",
    "get_logger",
    "log_excluded_record",
    "log_species_exclusion_summary",
    "log_validation_failure",
    # Stats
    "calculate_metrics",
    "calculate_baseline_r2",
    "delta_r2",
    "permutation_test",
    "stratified_permutation_test",
]
