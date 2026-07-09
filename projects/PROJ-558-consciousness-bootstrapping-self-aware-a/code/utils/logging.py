"""
Logging and Error Handling Infrastructure for the Consciousness Bootstrapping Project.

This module provides a centralized logging configuration and custom exception classes
to ensure consistent error reporting and debugging across the pipeline.
"""

import logging
import sys
import os
from pathlib import Path
from typing import Optional


# Custom Exception Hierarchy
class ConsciousnessBootstrappingError(Exception):
    """Base exception for all project-specific errors."""
    pass


class ConfigurationError(ConsciousnessBootstrappingError):
    """Raised when configuration validation fails."""
    pass


class DataLoadError(ConsciousnessBootstrappingError):
    """Raised when dataset fetching or processing fails."""
    pass


class ModelTrainingError(ConsciousnessBootstrappingError):
    """Raised when model training encounters a fatal error (e.g., OOM)."""
    pass


class EvaluationError(ConsciousnessBootstrappingError):
    """Raised when benchmark evaluation fails."""
    pass


class RecursionDepthError(ConsciousnessBootstrappingError):
    """Raised when recursion depth constraints are violated."""
    pass


# Logging Configuration
_log_initialized = False
_log_file_path: Optional[Path] = None


def setup_logging(
    log_level: int = logging.INFO,
    log_file: Optional[str] = None,
    project_root: Optional[Path] = None
) -> logging.Logger:
    """
    Configure the root logger for the project.

    Args:
        log_level: The logging level (e.g., logging.DEBUG, logging.INFO).
        log_file: Optional relative path for a log file (e.g., 'artifacts/results/run.log').
        project_root: Optional Path to the project root. If None, defaults to current working dir.

    Returns:
        The configured root logger instance.
    """
    global _log_initialized, _log_file_path

    if _log_initialized:
        return logging.getLogger("consciousness_pipeline")

    logger = logging.getLogger("consciousness_pipeline")
    logger.setLevel(log_level)

    # Prevent adding handlers multiple times if called again in same process
    if logger.handlers:
        logger.handlers.clear()

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File Handler (Optional)
    if log_file:
        if project_root is None:
            project_root = Path.cwd()
        
        log_path = project_root / log_file
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        _log_file_path = log_path

    _log_initialized = True
    logger.info("Logging infrastructure initialized.")
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieve a child logger of the project root.

    Args:
        name: Optional suffix for the logger name (e.g., 'training', 'evaluation').

    Returns:
        A logger instance configured with the project's handlers.
    """
    if name:
        return logging.getLogger(f"consciousness_pipeline.{name}")
    return logging.getLogger("consciousness_pipeline")


def log_exception(
    logger: logging.Logger,
    exc: Exception,
    context: str = "An unexpected error occurred"
) -> None:
    """
    Log an exception with full traceback context.

    Args:
        logger: The logger instance to use.
        exc: The exception instance.
        context: A brief description of what was happening when the error occurred.
    """
    import traceback
    tb_str = traceback.format_exc()
    logger.error(f"{context}: {type(exc).__name__}: {exc}")
    logger.debug(f"Traceback:\n{tb_str}")


# Convenience wrappers for common operations
def log_training_start(config_dict: dict) -> None:
    """Logs the start of a training run with key configuration parameters."""
    logger = get_logger("training")
    logger.info("Training run starting.")
    logger.info(f"Config: {config_dict}")


def log_training_end(
    checkpoint_path: Optional[str],
    final_loss: Optional[float] = None,
    success: bool = True
) -> None:
    """Logs the end of a training run."""
    logger = get_logger("training")
    if success:
        logger.info(f"Training completed successfully. Checkpoint: {checkpoint_path}, Final Loss: {final_loss}")
    else:
        logger.error("Training failed. Checkpoint may be incomplete.")


def log_evaluation_start(dataset_name: str) -> None:
    """Logs the start of an evaluation run."""
    logger = get_logger("evaluation")
    logger.info(f"Evaluation starting on dataset: {dataset_name}")


def log_metric(name: str, value: float) -> None:
    """Logs a specific metric result."""
    logger = get_logger("evaluation")
    logger.info(f"Metric: {name} = {value}")