"""
Utility modules for the plant root architecture prediction pipeline.

This package provides shared functionality including:
- Statistical analysis tools (stats.py)
- Geocoding and coordinate validation (geocoding.py)
- Custom exceptions for data quality issues (exceptions.py)
- Logging utilities (logging_utils.py)
- Environment configuration management (config.py)
"""

from .exceptions import DataQualityError, GeocodingError, SpeciesFilterError
from .stats import (
    calculate_metrics,
    calculate_baseline_r2,
    delta_r2,
    permutation_test,
    stratified_permutation_test,
)
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
from .config import (
    Config,
    load_environment,
    get_env,
    get_config,
    validate_config,
)

__all__ = [
    # Exceptions
    "DataQualityError",
    "GeocodingError",
    "SpeciesFilterError",
    # Stats
    "calculate_metrics",
    "calculate_baseline_r2",
    "delta_r2",
    "permutation_test",
    "stratified_permutation_test",
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
    # Config
    "Config",
    "load_environment",
    "get_env",
    "get_config",
    "validate_config",
]