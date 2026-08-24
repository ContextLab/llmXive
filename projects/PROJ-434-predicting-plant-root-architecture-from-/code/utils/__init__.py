"""
Utilities package for the root architecture prediction pipeline.
"""
from .exceptions import DataQualityError, GeocodingError, SpeciesFilterError
from .stats import calculate_metrics, calculate_baseline_r2, delta_r2, permutation_test, stratified_permutation_test
from .geocoding import validate_coordinates, align_crs, transform_coordinates, get_central_meridian, is_valid_crs, get_utm_zone, get_utm_crs
from .logging_utils import setup_logging, get_logger, log_excluded_record, log_species_exclusion_summary, log_validation_failure
from .config import Config, load_environment, get_env, get_config, validate_config

__all__ = [
    "DataQualityError", "GeocodingError", "SpeciesFilterError",
    "calculate_metrics", "calculate_baseline_r2", "delta_r2", "permutation_test", "stratified_permutation_test",
    "validate_coordinates", "align_crs", "transform_coordinates", "get_central_meridian", "is_valid_crs", "get_utm_zone", "get_utm_crs",
    "setup_logging", "get_logger", "log_excluded_record", "log_species_exclusion_summary", "log_validation_failure",
    "Config", "load_environment", "get_env", "get_config", "validate_config"
]
