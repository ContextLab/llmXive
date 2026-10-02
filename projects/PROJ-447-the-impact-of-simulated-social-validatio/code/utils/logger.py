"""
Logging infrastructure for the research pipeline.

This module provides a centralized logging setup and helper functions
for logging specific pipeline steps.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from .config import get_config


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance configured for the pipeline.

    Args:
        name: Name of the logger (usually __name__).

    Returns:
        Configured Logger instance.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    ch.setFormatter(formatter)

    logger.addHandler(ch)
    return logger


def log_data_load_start() -> None:
    """Log the start of data loading."""
    logger = get_logger(__name__)
    logger.info("Pipeline Step: Data Load Started")


def log_data_load_success(source: str) -> None:
    """Log successful data loading."""
    logger = get_logger(__name__)
    logger.info(f"Pipeline Step: Data Load Successful from {source}")


def log_data_load_error(message: str) -> None:
    """Log data loading failure."""
    logger = get_logger(__name__)
    logger.error(f"Pipeline Step: Data Load Failed - {message}")


def log_validation_start() -> None:
    """Log the start of validation."""
    logger = get_logger(__name__)
    logger.info("Pipeline Step: Validation Started")


def log_validation_success() -> None:
    """Log successful validation."""
    logger = get_logger(__name__)
    logger.info("Pipeline Step: Validation Successful")


def log_validation_failure(reason: str) -> None:
    """Log validation failure."""
    logger = get_logger(__name__)
    logger.error(f"Pipeline Step: Validation Failed - {reason}")


def log_model_fit_start(model_name: str) -> None:
    """Log the start of model fitting."""
    logger = get_logger(__name__)
    logger.info(f"Pipeline Step: Model Fit Started ({model_name})")


def log_model_fit_success(model_name: str) -> None:
    """Log successful model fitting."""
    logger = get_logger(__name__)
    logger.info(f"Pipeline Step: Model Fit Successful ({model_name})")


def log_model_fit_error(model_name: str, error: str) -> None:
    """Log model fitting failure."""
    logger = get_logger(__name__)
    logger.error(f"Pipeline Step: Model Fit Failed ({model_name}) - {error}")


def log_pipeline_step(step_name: str) -> None:
    """Log a generic pipeline step."""
    logger = get_logger(__name__)
    logger.info(f"Pipeline Step: {step_name}")
