"""
Logging configuration for the llmXive pipeline.
Provides file rotation, JSON logging for metrics, and standard loggers.
"""
import logging
import logging.handlers
import json
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, Union
from datetime import datetime

# Constants
DEFAULT_LOG_DIR = "logs"
DEFAULT_LOG_LEVEL = logging.INFO
LOG_FORMATTER_STRING = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
MAX_BYTES = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 5


class JSONFormatter(logging.Formatter):
    """Custom formatter for JSON logging, suitable for metrics parsing."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "metrics"):
            log_data["metrics"] = record.metrics

        return json.dumps(log_data)


class MetricsHandler(logging.Handler):
    """
    A logging handler that extracts metrics from log records and stores them.
    This is useful for aggregating metrics without cluttering standard logs.
    """

    def __init__(self, metrics_store: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.metrics_store = metrics_store if metrics_store is not None else {}

    def emit(self, record: logging.LogRecord):
        if hasattr(record, "metrics"):
            metric_name = getattr(record, "metric_name", "unknown_metric")
            if metric_name not in self.metrics_store:
                self.metrics_store[metric_name] = []
            self.metrics_store[metric_name].append(record.metrics)


def get_logger(
    name: str,
    log_file: Optional[str] = None,
    level: int = DEFAULT_LOG_LEVEL,
    json_logging: bool = False,
    log_dir: Optional[Union[str, Path]] = None,
) -> logging.Logger:
    """
    Create and configure a logger with optional file rotation and JSON formatting.

    Args:
        name: Name of the logger.
        log_file: Relative path to the log file (e.g., 'pipeline.log').
        level: Logging level (e.g., logging.INFO).
        json_logging: If True, use JSONFormatter for file output.
        log_dir: Directory to store logs. Defaults to DEFAULT_LOG_DIR.

    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers multiple times if called repeatedly
    if logger.hasHandlers():
        logger.handlers.clear()

    # Ensure log directory exists
    effective_log_dir = Path(log_dir) if log_dir else Path(DEFAULT_LOG_DIR)
    effective_log_dir.mkdir(parents=True, exist_ok=True)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(LOG_FORMATTER_STRING)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File Handler (RotatingFileHandler)
    if log_file:
        log_path = effective_log_dir / log_file
        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=MAX_BYTES,
            backupCount=BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setLevel(level)

        if json_logging:
            file_handler.setFormatter(JSONFormatter())
        else:
            file_handler.setFormatter(logging.Formatter(LOG_FORMATTER_STRING))

        logger.addHandler(file_handler)

    return logger


def log_metric(
    logger: logging.Logger,
    metric_name: str,
    value: float,
    step: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log a metric value to the logger.
    Adds the metric to the record for potential custom handlers.
    """
    metrics_payload = {
        "name": metric_name,
        "value": value,
        "step": step,
        "metadata": metadata or {},
    }

    record = logger.makeRecord(
        logger.name,
        logging.INFO,
        "",
        0,
        f"Metric: {metric_name} = {value}",
        (),
        None,
    )
    record.metrics = metrics_payload
    record.metric_name = metric_name
    logger.handle(record)


def log_metric_value(
    logger: logging.Logger,
    metric_name: str,
    value: float,
    step: Optional[int] = None,
) -> None:
    """
    Convenience wrapper for log_metric with minimal metadata.
    """
    log_metric(logger, metric_name, value, step)


def setup_default_loggers(
    project_root: Optional[Union[str, Path]] = None,
    log_level: int = DEFAULT_LOG_LEVEL,
) -> logging.Logger:
    """
    Set up default loggers for the project.
    Creates a main logger and a metrics-specific logger.

    Args:
        project_root: Root directory of the project. Defaults to current working directory.
        log_level: Global log level.

    Returns:
        The main project logger.
    """
    root_path = Path(project_root) if project_root else Path.cwd()
    log_dir = root_path / DEFAULT_LOG_DIR
    log_dir.mkdir(parents=True, exist_ok=True)

    # Main Logger
    main_logger = get_logger(
        name="llmXive",
        log_file="pipeline.log",
        level=log_level,
        log_dir=log_dir,
    )

    # Metrics Logger (JSON format)
    metrics_logger = get_logger(
        name="llmXive.metrics",
        log_file="metrics.jsonl",
        level=log_level,
        json_logging=True,
        log_dir=log_dir,
    )

    return main_logger


def get_default_logger() -> logging.Logger:
    """
    Retrieve the main default logger.
    Note: This assumes setup_default_loggers has been called or relies on
    the root logger if not explicitly set up.
    """
    return logging.getLogger("llmXive")


def info(logger: logging.Logger, msg: str, *args, **kwargs) -> None:
    """Convenience function for logger.info."""
    logger.info(msg, *args, **kwargs)


def debug(logger: logging.Logger, msg: str, *args, **kwargs) -> None:
    """Convenience function for logger.debug."""
    logger.debug(msg, *args, **kwargs)


def warning(logger: logging.Logger, msg: str, *args, **kwargs) -> None:
    """Convenience function for logger.warning."""
    logger.warning(msg, *args, **kwargs)


def error(logger: logging.Logger, msg: str, *args, **kwargs) -> None:
    """Convenience function for logger.error."""
    logger.error(msg, *args, **kwargs)


def critical(logger: logging.Logger, msg: str, *args, **kwargs) -> None:
    """Convenience function for logger.critical."""
    logger.critical(msg, *args, **kwargs)


def main() -> None:
    """
    Demonstration of logging setup and usage.
    """
    # Initialize default loggers
    logger = setup_default_loggers()

    info(logger, "Pipeline starting...")
    debug(logger, "Debugging detailed operations.")
    warning(logger, "This is a warning message.")
    error(logger, "An error occurred during processing.")

    # Log a metric
    log_metric(logger, "loss", 0.5, step=1, metadata={"batch": 10})
    log_metric(logger, "accuracy", 0.85, step=1)

    # Log to metrics logger specifically
    metrics_logger = logging.getLogger("llmXive.metrics")
    info(metrics_logger, "Checkpoint saved.", extra={"metrics": {"epoch": 1}})

    print("Logging demo completed. Check 'logs/' directory.")


if __name__ == "__main__":
    main()
