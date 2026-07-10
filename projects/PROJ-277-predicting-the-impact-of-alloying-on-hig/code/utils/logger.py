"""
Logging infrastructure and error code definitions for the oxidation resistance prediction pipeline.

This module provides:
- Standardized logging configuration
- Error code constants for consistent exit behavior
- Utility functions for structured logging
"""

import logging
import sys
import os
from datetime import datetime
from typing import Optional

# ============================================================================
# ERROR CODES
# ============================================================================

EXIT_CODE_SUCCESS = 0
EXIT_CODE_GENERAL_FAILURE = 1
EXIT_CODE_CONFIG_ERROR = 2
EXIT_CODE_DATA_VALIDATION_FAILURE = 3
EXIT_CODE_MODEL_TRAINING_FAILURE = 4
EXIT_CODE_DATA_FETCH_FAILURE = 5
EXIT_CODE_IO_ERROR = 6

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

_logger: Optional[logging.Logger] = None

def configure_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    mode: str = "local"
) -> logging.Logger:
    """
    Configure and return the project logger.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file. If None, logs only to stdout.
        mode: Execution mode ('ci' or 'local'). Affects log verbosity.
    
    Returns:
        Configured logger instance.
    
    Side Effects:
        - Configures root logger
        - Creates log file if log_file is provided
        - Sets up console and file handlers
    """
    global _logger
    
    if _logger is not None:
        return _logger
    
    # Create logger
    _logger = logging.getLogger("llmXive.oxidation")
    _logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear any existing handlers
    _logger.handlers.clear()
    
    # Formatter
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(log_format, date_format)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    _logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        # Ensure directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        _logger.addHandler(file_handler)
    
    # Adjust verbosity for CI mode
    if mode == "ci":
        _logger.setLevel(logging.WARNING)
        # Remove console handler for CI if we want quieter logs
        # _logger.removeHandler(console_handler)
    
    _logger.info("Logging infrastructure initialized.")
    _logger.info(f"Mode: {mode}, Log level: {log_level}")
    
    return _logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get the project logger, optionally with a child namespace.
    
    Args:
        name: Optional child namespace (e.g., "data.fetcher")
    
    Returns:
        Logger instance.
    
    Raises:
        RuntimeError: If logging has not been configured yet.
    """
    global _logger
    
    if _logger is None:
        # Auto-configure with defaults if not explicitly configured
        _logger = configure_logging()
    
    if name:
        return _logger.getChild(name)
    return _logger

def log_startup_info(mode: str, config: dict) -> None:
    """
    Log standardized startup information for reproducibility.
    
    Args:
        mode: Execution mode ('ci' or 'local')
        config: Configuration dictionary to log
    """
    logger = get_logger()
    timestamp = datetime.now().isoformat()
    
    logger.info("=" * 60)
    logger.info("PIPELINE STARTUP")
    logger.info("=" * 60)
    logger.info(f"Timestamp: {timestamp}")
    logger.info(f"Mode: {mode}")
    logger.info(f"Working directory: {os.getcwd()}")
    
    logger.info("Configuration:")
    for key, value in config.items():
        logger.info(f"  {key}: {value}")
    
    logger.info("=" * 60)

def log_data_validation_failure(
    reason: str,
    sample_count: Optional[int] = None,
    missing_fields: Optional[list] = None
) -> None:
    """
    Log a data validation failure with structured details.
    
    Args:
        reason: Primary reason for validation failure
        sample_count: Number of samples inspected
        missing_fields: List of missing required fields
    """
    logger = get_logger("data.validation")
    logger.error(f"DATA VALIDATION FAILURE: {reason}")
    
    if sample_count is not None:
        logger.error(f"Samples inspected: {sample_count}")
    
    if missing_fields:
        logger.error(f"Missing fields: {', '.join(missing_fields)}")
    
    logger.error(f"Exiting with code: {EXIT_CODE_DATA_VALIDATION_FAILURE}")

def log_model_training_failure(
    model_name: str,
    reason: str,
    exception: Optional[Exception] = None
) -> None:
    """
    Log a model training failure.
    
    Args:
        model_name: Name of the model that failed
        reason: Description of the failure
        exception: Optional exception instance for traceback
    """
    logger = get_logger("models")
    logger.error(f"MODEL TRAINING FAILURE: {model_name}")
    logger.error(f"Reason: {reason}")
    
    if exception:
        logger.exception("Exception details:")
    
    logger.error(f"Exiting with code: {EXIT_CODE_MODEL_TRAINING_FAILURE}")

def log_synthetic_fallback_trigger(
    reason: str,
    report_path: str
) -> None:
    """
    Log when synthetic data fallback is triggered.
    
    Args:
        reason: Why real data was unavailable
        report_path: Path to the generated gap report
    """
    logger = get_logger("data.fallback")
    logger.warning("SYNTHETIC DATA FALLBACK TRIGGERED")
    logger.warning(f"Reason: {reason}")
    logger.warning(f"Gap report written to: {report_path}")
    logger.warning("All subsequent results are based on synthetic data.")
    logger.warning("Scientific validity warnings will be applied to outputs.")

def log_gap_analysis_result(report: dict) -> None:
    """
    Log gap analysis results.
    
    Args:
        report: GapAnalysisReport dictionary
    """
    logger = get_logger("models.evaluator")
    logger.info("GAP ANALYSIS RESULTS")
    logger.info(f"  Composition-only RMSE: {report.get('composition_only_rmse', 'N/A')}")
    logger.info(f"  Augmented RMSE: {report.get('augmented_rmse', 'N/A')}")
    logger.info(f"  Error reduction: {report.get('error_reduction_pct', 'N/A')}%")
    
    sensitive = report.get('sensitive_samples', [])
    if sensitive:
        logger.info(f"  High sensitivity samples: {len(sensitive)}")
        logger.info(f"    Sample IDs: {', '.join(sensitive[:5])}{'...' if len(sensitive) > 5 else ''}")
    else:
        logger.info("  No high sensitivity samples detected.")

def log_prediction_output(output_path: str, count: int) -> None:
    """
    Log successful prediction output generation.
    
    Args:
        output_path: Path to the generated predictions file
        count: Number of predictions generated
    """
    logger = get_logger("main")
    logger.info(f"Predictions written to: {output_path}")
    logger.info(f"Total predictions: {count}")

def log_final_summary(
    status: str,
    exit_code: int,
    duration_seconds: float
) -> None:
    """
    Log final pipeline summary.
    
    Args:
        status: 'SUCCESS' or 'FAILURE'
        exit_code: Final exit code
        duration_seconds: Total pipeline duration
    """
    logger = get_logger()
    logger.info("=" * 60)
    logger.info("PIPELINE SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Status: {status}")
    logger.info(f"Exit code: {exit_code}")
    logger.info(f"Duration: {duration_seconds:.2f} seconds")
    logger.info("=" * 60)
