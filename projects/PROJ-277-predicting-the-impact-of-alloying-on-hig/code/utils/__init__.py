"""
Utility modules for the oxidation resistance prediction pipeline.
"""

from .logger import (
    configure_logging,
    get_logger,
    log_startup_info,
    log_data_validation_failure,
    log_model_training_failure,
    log_synthetic_fallback_trigger,
    log_gap_analysis_result,
    log_prediction_output,
    log_final_summary,
    EXIT_CODE_SUCCESS,
    EXIT_CODE_GENERAL_FAILURE,
    EXIT_CODE_CONFIG_ERROR,
    EXIT_CODE_DATA_VALIDATION_FAILURE,
    EXIT_CODE_MODEL_TRAINING_FAILURE,
    EXIT_CODE_DATA_FETCH_FAILURE,
    EXIT_CODE_IO_ERROR,
)

__all__ = [
    "configure_logging",
    "get_logger",
    "log_startup_info",
    "log_data_validation_failure",
    "log_model_training_failure",
    "log_synthetic_fallback_trigger",
    "log_gap_analysis_result",
    "log_prediction_output",
    "log_final_summary",
    "EXIT_CODE_SUCCESS",
    "EXIT_CODE_GENERAL_FAILURE",
    "EXIT_CODE_CONFIG_ERROR",
    "EXIT_CODE_DATA_VALIDATION_FAILURE",
    "EXIT_CODE_MODEL_TRAINING_FAILURE",
    "EXIT_CODE_DATA_FETCH_FAILURE",
    "EXIT_CODE_IO_ERROR",
]