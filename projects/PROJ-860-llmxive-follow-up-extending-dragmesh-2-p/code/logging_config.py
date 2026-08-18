"""
Logging configuration module for the llmXive Virtual Tactile Zero-Shot Adaptation pipeline.

This module provides centralized logging setup for all pipeline components, ensuring
consistent log formatting, file paths, and log levels across the project.

Per task T016a: Implements specific file paths and formats for training, evaluation,
aggregation, analysis, and benchmark logging.
"""

import os
import sys
import logging
import logging.handlers
from pathlib import Path
from typing import Optional, Dict, Any

# Project root relative to this file (code/)
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
LOG_DIR = PROJECT_ROOT / "data" / "logs"

# Ensure log directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Standard log format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Specific log file paths per task requirements
LOG_FILES = {
    "training": LOG_DIR / "training.log",
    "evaluation": LOG_DIR / "evaluation.log",
    "aggregation": LOG_DIR / "aggregation.log",
    "analysis": LOG_DIR / "analysis.log",
    "benchmark": LOG_DIR / "benchmark.log",
    "pipeline": LOG_DIR / "pipeline.log",
}

# Log levels
DEFAULT_LEVEL = logging.INFO
DEBUG_LEVEL = logging.DEBUG
WARNING_LEVEL = logging.WARNING
ERROR_LEVEL = logging.ERROR

# Cache for created loggers to avoid reconfiguration
_logger_cache: Dict[str, logging.Logger] = {}


def _get_formatter() -> logging.Formatter:
    """Return the standard formatter for this project."""
    return logging.Formatter(LOG_FORMAT, DATE_FORMAT)


def _setup_file_handler(logger: logging.Logger, log_file: Path, level: int = DEFAULT_LEVEL) -> None:
    """
    Configure a rotating file handler for a logger.

    Args:
        logger: The logger to configure.
        log_file: Path to the log file.
        level: Log level for the handler.
    """
    # Ensure parent directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Rotating file handler: max 10MB, keep 5 backup files
    handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8"
    )
    handler.setLevel(level)
    handler.setFormatter(_get_formatter())

    # Avoid adding duplicate handlers
    if not any(isinstance(h, logging.handlers.RotatingFileHandler) for h in logger.handlers):
        logger.addHandler(handler)


def _setup_console_handler(logger: logging.Logger, level: int = DEFAULT_LEVEL) -> None:
    """
    Configure a console handler for a logger.

    Args:
        logger: The logger to configure.
        level: Log level for the handler.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(_get_formatter())

    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        logger.addHandler(handler)


def get_logger(name: str, level: int = DEFAULT_LEVEL, log_to_file: bool = True) -> logging.Logger:
    """
    Get or create a logger with the given name.

    Args:
        name: Logger name (typically __name__ of the module).
        level: Minimum log level.
        log_to_file: Whether to add a file handler.

    Returns:
        Configured logger instance.
    """
    if name in _logger_cache:
        return _logger_cache[name]

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False  # Prevent duplicate logs in parent loggers

    if log_to_file:
        # Default to pipeline.log if no specific file is mapped
        log_file = LOG_FILES.get("pipeline", LOG_DIR / "pipeline.log")
        _setup_file_handler(logger, log_file, level)

    _setup_console_handler(logger, level)

    _logger_cache[name] = logger
    return logger


def get_logger_for_module(module_name: str, level: int = DEFAULT_LEVEL) -> logging.Logger:
    """
    Convenience wrapper for get_logger using the module's __name__.

    Args:
        module_name: The module name (e.g., __name__).
        level: Log level.

    Returns:
        Configured logger.
    """
    return get_logger(module_name, level)


def setup_training_logger(level: int = DEFAULT_LEVEL) -> logging.Logger:
    """
    Setup the training-specific logger.

    Logs training progress, reward adjustments, k_est values, and episode results.
    File: data/logs/training.log

    Args:
        level: Log level.

    Returns:
        Training logger.
    """
    logger = get_logger("training", level, log_to_file=False)
    _setup_file_handler(logger, LOG_FILES["training"], level)
    return logger


def setup_evaluation_logger(level: int = DEFAULT_LEVEL) -> logging.Logger:
    """
    Setup the evaluation-specific logger.

    Logs evaluation metrics, success rates, and policy comparisons.
    File: data/logs/evaluation.log

    Args:
        level: Log level.

    Returns:
        Evaluation logger.
    """
    logger = get_logger("evaluation", level, log_to_file=False)
    _setup_file_handler(logger, LOG_FILES["evaluation"], level)
    return logger


def setup_aggregation_logger(level: int = DEFAULT_LEVEL) -> logging.Logger:
    """
    Setup the aggregation-specific logger.

    Logs data aggregation steps, record validation, and CSV writes.
    File: data/logs/aggregation.log

    Args:
        level: Log level.

    Returns:
        Aggregation logger.
    """
    logger = get_logger("aggregation", level, log_to_file=False)
    _setup_file_handler(logger, LOG_FILES["aggregation"], level)
    return logger


def setup_analysis_logger(level: int = DEFAULT_LEVEL) -> logging.Logger:
    """
    Setup the analysis-specific logger.

    Logs statistical test results, p-values, and power calculations.
    File: data/logs/analysis.log

    Args:
        level: Log level.

    Returns:
        Analysis logger.
    """
    logger = get_logger("analysis", level, log_to_file=False)
    _setup_file_handler(logger, LOG_FILES["analysis"], level)
    return logger


def setup_benchmark_logger(level: int = DEFAULT_LEVEL) -> logging.Logger:
    """
    Setup the benchmark-specific logger.

    Logs wall-clock times, memory usage, and pipeline component performance.
    File: data/logs/benchmark.log

    Args:
        level: Log level.

    Returns:
        Benchmark logger.
    """
    logger = get_logger("benchmark", level, log_to_file=False)
    _setup_file_handler(logger, LOG_FILES["benchmark"], level)
    return logger


def setup_all_loggers(level: int = DEFAULT_LEVEL) -> Dict[str, logging.Logger]:
    """
    Initialize all specialized loggers at once.

    Args:
        level: Log level for all loggers.

    Returns:
        Dictionary mapping logger names to logger instances.
    """
    return {
        "training": setup_training_logger(level),
        "evaluation": setup_evaluation_logger(level),
        "aggregation": setup_aggregation_logger(level),
        "analysis": setup_analysis_logger(level),
        "benchmark": setup_benchmark_logger(level),
        "pipeline": get_logger("pipeline", level),
    }


def init_logging(level: int = DEFAULT_LEVEL) -> None:
    """
    Initialize the root logging configuration for the entire pipeline.

    This should be called once at the entry point of any script to ensure
    consistent logging behavior.

    Args:
        level: Global log level.
    """
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    # Ensure our log directory exists
    LOG_DIR.mkdir(parents=True, exist_ok=True)