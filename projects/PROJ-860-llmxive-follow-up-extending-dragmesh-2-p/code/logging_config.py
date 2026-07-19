"""
Logging configuration for the llmXive Virtual Tactile Adaptation pipeline.

This module provides centralized logging setup for all major pipeline components:
- Training (train.py)
- Evaluation (evaluate.py)
- Aggregation (aggregate.py)
- Analysis (analysis.py)
- Benchmarking (benchmark_runner.py)

Log files are written to the 'state/logs' directory relative to the project root,
with specific subdirectories for each component to maintain separation of concerns.
"""

import os
import sys
import logging
import logging.handlers
from pathlib import Path
from typing import Optional, Dict, Any

# Define project root relative to this file's location
# Assuming this file is at: projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/logging_config.py
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_LOG_DIR = _PROJECT_ROOT / "state" / "logs"

# Ensure log directory exists
_LOG_DIR.mkdir(parents=True, exist_ok=True)

# Default log format
_DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Log file paths
_LOG_FILES: Dict[str, Path] = {
    "training": _LOG_DIR / "training.log",
    "evaluation": _LOG_DIR / "evaluation.log",
    "aggregation": _LOG_DIR / "aggregation.log",
    "analysis": _LOG_DIR / "analysis.log",
    "benchmark": _LOG_DIR / "benchmark.log",
    "general": _LOG_DIR / "general.log",
}

# Maximum log file size (10 MB) before rotation
_MAX_BYTES = 10 * 1024 * 1024
# Number of backup files to keep
_BACKUP_COUNT = 5

# Global logger registry
_LOGGERS: Dict[str, logging.Logger] = {}


def _get_formatter() -> logging.Formatter:
    """Create a standard log formatter."""
    return logging.Formatter(fmt=_DEFAULT_FORMAT, datefmt=_DATE_FORMAT)


def _setup_file_handler(log_path: Path) -> logging.handlers.RotatingFileHandler:
    """
    Create a rotating file handler for the given log path.

    Args:
        log_path: Path to the log file.

    Returns:
        A configured RotatingFileHandler.
    """
    # Ensure parent directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    handler = logging.handlers.RotatingFileHandler(
        log_path,
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8"
    )
    handler.setFormatter(_get_formatter())
    handler.setLevel(logging.DEBUG)
    return handler


def _setup_console_handler() -> logging.StreamHandler:
    """
    Create a console handler for stdout.

    Returns:
        A configured StreamHandler.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_get_formatter())
    handler.setLevel(logging.INFO)
    return handler


def get_logger(name: str, log_file: Optional[Path] = None) -> logging.Logger:
    """
    Get or create a logger with the given name.

    If a log file is provided, a file handler is attached to the logger.
    A console handler is always attached for visibility.

    Args:
        name: Logger name (typically __name__ of the module).
        log_file: Optional path to a log file.

    Returns:
        A configured logging.Logger instance.
    """
    if name in _LOGGERS:
        return _LOGGERS[name]

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Avoid adding handlers multiple times if called repeatedly
    if logger.handlers:
        logger.handlers.clear()

    # Add console handler
    console_handler = _setup_console_handler()
    logger.addHandler(console_handler)

    # Add file handler if specified
    if log_file:
        file_handler = _setup_file_handler(log_file)
        logger.addHandler(file_handler)

    logger.propagate = False

    _LOGGERS[name] = logger
    return logger


def setup_training_logger() -> logging.Logger:
    """
    Setup and return the training logger.

    Returns:
        Configured logger for training operations.
    """
    return get_logger("training", _LOG_FILES["training"])


def setup_evaluation_logger() -> logging.Logger:
    """
    Setup and return the evaluation logger.

    Returns:
        Configured logger for evaluation operations.
    """
    return get_logger("evaluation", _LOG_FILES["evaluation"])


def setup_aggregation_logger() -> logging.Logger:
    """
    Setup and return the aggregation logger.

    Returns:
        Configured logger for aggregation operations.
    """
    return get_logger("aggregation", _LOG_FILES["aggregation"])


def setup_analysis_logger() -> logging.Logger:
    """
    Setup and return the analysis logger.

    Returns:
        Configured logger for analysis operations.
    """
    return get_logger("analysis", _LOG_FILES["analysis"])


def setup_benchmark_logger() -> logging.Logger:
    """
    Setup and return the benchmark logger.

    Returns:
        Configured logger for benchmark operations.
    """
    return get_logger("benchmark", _LOG_FILES["benchmark"])


def setup_all_loggers() -> Dict[str, logging.Logger]:
    """
    Setup all standard loggers and return them as a dictionary.

    Returns:
        Dictionary mapping component names to their loggers.
    """
    return {
        "training": setup_training_logger(),
        "evaluation": setup_evaluation_logger(),
        "aggregation": setup_aggregation_logger(),
        "analysis": setup_analysis_logger(),
        "benchmark": setup_benchmark_logger(),
    }


def init_logging() -> Dict[str, logging.Logger]:
    """
    Initialize all loggers for the pipeline.

    This function should be called at the entry point of any pipeline component
    to ensure consistent logging configuration.

    Returns:
        Dictionary of initialized loggers.
    """
    return setup_all_loggers()


# Convenience function for ad-hoc logging
def get_logger_for_module(module_name: str, component: Optional[str] = None) -> logging.Logger:
    """
    Get a logger configured for a specific module and optional component.

    Args:
        module_name: The __name__ of the module requesting the logger.
        component: Optional component name (e.g., 'training', 'evaluation') to
                   select the appropriate log file. If None, uses 'general'.

    Returns:
        Configured logger instance.
    """
    component = component or "general"
    log_file = _LOG_FILES.get(component, _LOG_FILES["general"])
    return get_logger(module_name, log_file)