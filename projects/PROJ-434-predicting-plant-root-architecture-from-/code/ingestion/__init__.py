"""
Ingestion module for the plant root architecture prediction pipeline.

This module handles:
- Soil data extraction from geospatial rasters
- Trait data loading and validation
- Dataset merging and filtering
- Data validation and quality checks
- Output generation and logging
"""

from .soil_data import load_soil_raster, extract_values_at_coords, process_soil_data, main
from .trait_data import load_trait_data, validate_units, filter_physically_plausible, main as trait_main
from .merge import load_soil_data, load_trait_data, merge_datasets, apply_species_filter, main as merge_main
from .validation import calculate_match_proportion, filter_valid_rows, validate_soil_data_coverage, main as validation_main
from .logging_utils import setup_logging, get_logger, log_excluded_record, log_species_exclusion_summary, log_validation_failure
from .generate_outputs import count_valid_observations, generate_exclusion_summary, main as outputs_main

__all__ = [
    # Soil data
    "load_soil_raster",
    "extract_values_at_coords",
    "process_soil_data",
    "main",
    # Trait data
    "load_trait_data",
    "validate_units",
    "filter_physically_plausible",
    "trait_main",
    # Merge
    "load_soil_data",
    "merge_datasets",
    "apply_species_filter",
    "merge_main",
    # Validation
    "calculate_match_proportion",
    "filter_valid_rows",
    "validate_soil_data_coverage",
    "validation_main",
    # Logging
    "setup_logging",
    "get_logger",
    "log_excluded_record",
    "log_species_exclusion_summary",
    "log_validation_failure",
    # Outputs
    "count_valid_observations",
    "generate_exclusion_summary",
    "outputs_main",
]
