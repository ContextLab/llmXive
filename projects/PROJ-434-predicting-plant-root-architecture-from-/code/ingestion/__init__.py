"""
Ingestion package for data loading and processing.
"""
from .data_loader import DataFetchError, load_root_trait_data, main
from .trait_data import load_trait_data, validate_units, filter_physically_plausible, main as trait_main
from .soil_data import load_soil_raster, extract_values_at_coords, process_soil_data, main as soil_main
from .merge import load_soil_data, load_trait_data, merge_datasets, apply_species_filter, main as merge_main
from .validation import calculate_match_proportion, filter_valid_rows, validate_soil_data_coverage, main as validation_main
from .generate_outputs import count_valid_observations, generate_exclusion_summary, main as outputs_main
from .logging_utils import setup_logging, get_logger, log_excluded_record, log_species_exclusion_summary, log_validation_failure

__all__ = [
    "DataFetchError", "load_root_trait_data", "main",
    "load_trait_data", "validate_units", "filter_physically_plausible", "trait_main",
    "load_soil_raster", "extract_values_at_coords", "process_soil_data", "soil_main",
    "load_soil_data", "load_trait_data", "merge_datasets", "apply_species_filter", "merge_main",
    "calculate_match_proportion", "filter_valid_rows", "validate_soil_data_coverage", "validation_main",
    "count_valid_observations", "generate_exclusion_summary", "outputs_main",
    "setup_logging", "get_logger", "log_excluded_record", "log_species_exclusion_summary", "log_validation_failure"
]
