"""
Logging infrastructure for the llmXive research pipeline.

Provides a configured logger instance that tracks data loading,
validation, and model fitting steps with appropriate levels and
standardized formatting.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

# Import project config to determine log file paths if needed
from .config import get_config


# Define log levels as constants for clarity
LOG_LEVEL_DEBUG = logging.DEBUG
LOG_LEVEL_INFO = logging.INFO
LOG_LEVEL_WARNING = logging.WARNING
LOG_LEVEL_ERROR = logging.ERROR
LOG_LEVEL_CRITICAL = logging.CRITICAL

# Standard log format including timestamp, level, module, and message
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Global logger instance (singleton pattern)
_logger: Optional[logging.Logger] = None


def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Retrieve or create a configured logger instance.

    Args:
        name: The name of the logger (typically the module name).

    Returns:
        A configured logging.Logger instance.

    The logger is configured to:
    - Output to both console and a file (if configured)
    - Use consistent formatting
    - Respect the log level from configuration or environment
    """
    global _logger

    if _logger is None:
        # Create root logger
        _logger = logging.getLogger(name)
        _logger.setLevel(LOG_LEVEL_INFO)

        # Prevent adding handlers multiple times if called repeatedly
        if _logger.handlers:
            _logger.handlers.clear()

        # Get configuration
        config = get_config()
        log_level_str = config.get("log_level", "INFO").upper()
        log_file_path = config.get("log_file_path", "data/pipeline.log")

        # Map string level to logging constant
        level_map = {
            "DEBUG": LOG_LEVEL_DEBUG,
            "INFO": LOG_LEVEL_INFO,
            "WARNING": LOG_LEVEL_WARNING,
            "ERROR": LOG_LEVEL_ERROR,
            "CRITICAL": LOG_LEVEL_CRITICAL,
        }
        log_level = level_map.get(log_level_str, LOG_LEVEL_INFO)
        _logger.setLevel(log_level)

        # Create formatter
        formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        _logger.addHandler(console_handler)

        # File handler (ensure directory exists)
        try:
            log_path = Path(log_file_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_path, mode='a', encoding='utf-8')
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            _logger.addHandler(file_handler)
        except Exception as e:
            # Fallback if file logging fails, but don't crash
            _logger.warning(f"Failed to initialize file logging: {e}")

    return _logger


def log_data_load_start(dataset_name: str) -> None:
    """Log the start of a data loading operation."""
    logger = get_logger()
    logger.info(f"Starting data load for dataset: {dataset_name}")


def log_data_load_success(dataset_name: str, rows: int) -> None:
    """Log successful data loading."""
    logger = get_logger()
    logger.info(f"Data load successful for {dataset_name}: {rows} rows loaded")


def log_data_load_error(dataset_name: str, error_msg: str) -> None:
    """Log a data loading error."""
    logger = get_logger()
    logger.error(f"Data load failed for {dataset_name}: {error_msg}")


def log_validation_start(step_name: str) -> None:
    """Log the start of a validation step."""
    logger = get_logger()
    logger.info(f"Starting validation step: {step_name}")


def log_validation_success(step_name: str, details: str) -> None:
    """Log successful validation."""
    logger = get_logger()
    logger.info(f"Validation passed for {step_name}: {details}")


def log_validation_failure(step_name: str, details: str) -> None:
    """Log a validation failure."""
    logger = get_logger()
    logger.warning(f"Validation failed for {step_name}: {details}")


def log_model_fit_start(model_name: str) -> None:
    """Log the start of a model fitting operation."""
    logger = get_logger()
    logger.info(f"Starting model fit for: {model_name}")


def log_model_fit_success(model_name: str, metrics: dict) -> None:
    """Log successful model fitting."""
    logger = get_logger()
    metrics_str = ", ".join(f"{k}={v:.4f}" for k, v in metrics.items())
    logger.info(f"Model fit successful for {model_name}: {metrics_str}")


def log_model_fit_error(model_name: str, error_msg: str) -> None:
    """Log a model fitting error."""
    logger = get_logger()
    logger.error(f"Model fit failed for {model_name}: {error_msg}")


def log_pipeline_step(step_name: str, status: str, details: str = "") -> None:
    """
    Generic log function for pipeline steps.

    Args:
        step_name: Name of the pipeline step.
        status: Status of the step (e.g., 'STARTED', 'COMPLETED', 'FAILED').
        details: Optional additional details.
    """
    logger = get_logger()
    message = f"Pipeline Step [{step_name}]: {status}"
    if details:
        message += f" - {details}"

    if status == "FAILED":
        logger.error(message)
    elif status == "COMPLETED":
        logger.info(message)
    else:
        logger.info(message)