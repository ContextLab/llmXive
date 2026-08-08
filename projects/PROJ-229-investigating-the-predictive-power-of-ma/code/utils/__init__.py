"""
Utilities package for the llmXive pipeline.
"""
from .logger import setup_logger, get_pipeline_logger
from .error_handling import (
    PipelineError,
    DataFetchError,
    DataProcessingError,
    ModelTrainingError,
    ConfigError,
    handle_error,
    validate_not_null,
    validate_positive
)
from .create_data_dirs import create_data_directories
from .collinearity_utils import calculate_vif, identify_high_collinearity
from .stability_checks import check_nan_inf, get_memory_stats, check_memory_usage, validate_dataframe, validate_features
from .generate_dataset_schema import load_target_decision, generate_schema, validate_schema, save_schema
from .setup_data_dirs import create_data_dirs as setup_data_dirs_utils

__all__ = [
    "setup_logger",
    "get_pipeline_logger",
    "PipelineError",
    "DataFetchError",
    "DataProcessingError",
    "ModelTrainingError",
    "ConfigError",
    "handle_error",
    "validate_not_null",
    "validate_positive",
    "create_data_directories",
    "calculate_vif",
    "identify_high_collinearity",
    "check_nan_inf",
    "get_memory_stats",
    "check_memory_usage",
    "validate_dataframe",
    "validate_features",
    "load_target_decision",
    "generate_schema",
    "validate_schema",
    "save_schema",
    "setup_data_dirs_utils"
]