"""
Logging configuration for llmXive project.
Provides file rotation, JSON logging for metrics, and standard loggers.
"""
import logging
import logging.handlers
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, Union
from datetime import datetime

# Constants
DEFAULT_LOG_DIR = Path("data/logs")
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
DEFAULT_BACKUP_COUNT = 5


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs log records as JSON."""

    def __init__(self, include_extra: bool = True):
        super().__init__()
        self.include_extra = include_extra

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if self.include_extra:
            # Add extra fields if present
            extra_fields = {
                k: v for k, v in record.__dict__.items()
                if k not in ("name", "msg", "args", "created", "filename",
                             "funcName", "levelname", "levelno", "lineno",
                             "module", "msecs", "pathname", "process",
                             "processName", "relativeCreated", "stack_info",
                             "exc_info", "exc_text", "thread", "threadName",
                             "message", "taskName")
            }
            if extra_fields:
                log_data["extra"] = extra_fields

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


class MetricsHandler(logging.Handler):
    """
    Custom handler that extracts metric values from log records and stores them.
    Expected log format: log_metric("metric_name", value, extra={...})
    """

    def __init__(self, metrics_store: Optional[Path] = None):
        super().__init__()
        self.metrics_store = metrics_store
        self.metrics: Dict[str, list] = {}
        self.setFormatter(JSONFormatter())

    def emit(self, record: logging.LogRecord):
        try:
            # Check if this is a metric log
            if hasattr(record, "is_metric") and record.is_metric:
                metric_name = getattr(record, "metric_name", "unknown")
                metric_value = getattr(record, "metric_value", None)

                if metric_name not in self.metrics:
                    self.metrics[metric_name] = []

                self.metrics[metric_name].append({
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "value": metric_value,
                    "level": record.levelname,
                })

                # Save to file if store path is provided
                if self.metrics_store:
                    self._save_metrics()

        except Exception:
            self.handleError(record)

    def _save_metrics(self):
        """Save metrics to JSON file."""
        if self.metrics_store:
            self.metrics_store.parent.mkdir(parents=True, exist_ok=True)
            with open(self.metrics_store, "w") as f:
                json.dump(self.metrics, f, indent=2)

    def get_metrics(self) -> Dict[str, list]:
        """Return collected metrics."""
        return self.metrics.copy()


def get_logger(
    name: str,
    log_file: Optional[Union[str, Path]] = None,
    metrics_file: Optional[Union[str, Path]] = None,
    level: int = DEFAULT_LOG_LEVEL,
    max_bytes: int = DEFAULT_MAX_BYTES,
    backup_count: int = DEFAULT_BACKUP_COUNT,
    json_format: bool = False
) -> logging.Logger:
    """
    Create and configure a logger with optional file rotation and JSON formatting.

    Args:
        name: Logger name
        log_file: Path to log file (optional)
        metrics_file: Path to metrics JSON file (optional)
        level: Logging level
        max_bytes: Max bytes before rotation
        backup_count: Number of backup files to keep
        json_format: If True, use JSONFormatter

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)

    if json_format:
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))

    logger.addHandler(console_handler)

    # File handler with rotation
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(level)

        if json_format:
            file_handler.setFormatter(JSONFormatter())
        else:
            file_handler.setFormatter(logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            ))

        logger.addHandler(file_handler)

    # Metrics handler
    if metrics_file:
        metrics_handler = MetricsHandler(Path(metrics_file))
        metrics_handler.setLevel(level)
        logger.addHandler(metrics_handler)

    return logger


def log_metric(
    logger: logging.Logger,
    name: str,
    value: float,
    level: int = logging.INFO,
    **kwargs
) -> None:
    """
    Log a metric value with special handling for metrics tracking.

    Args:
        logger: Logger instance
        name: Metric name
        value: Metric value
        level: Logging level
        **kwargs: Additional extra fields to include
    """
    extra = {
        "is_metric": True,
        "metric_name": name,
        "metric_value": value,
        **kwargs
    }
    logger.log(level, f"Metric: {name} = {value}", extra=extra)


def log_metric_value(
    logger: logging.Logger,
    name: str,
    value: float,
    **kwargs
) -> None:
    """
    Convenience function to log a metric value at INFO level.

    Args:
        logger: Logger instance
        name: Metric name
        value: Metric value
        **kwargs: Additional extra fields
    """
    log_metric(logger, name, value, logging.INFO, **kwargs)


# Global logger instances
_loggers: Dict[str, logging.Logger] = {}
_metrics_handler: Optional[MetricsHandler] = None


def setup_default_loggers(
    log_dir: Optional[Union[str, Path]] = None,
    metrics_file: Optional[Union[str, Path]] = None,
    level: int = DEFAULT_LOG_LEVEL,
    json_format: bool = True
) -> None:
    """
    Set up default loggers for the project.

    Args:
        log_dir: Directory for log files
        metrics_file: Path to metrics JSON file
        level: Logging level
        json_format: Use JSON formatting
    """
    global _loggers, _metrics_handler

    if log_dir is None:
        log_dir = DEFAULT_LOG_DIR
    else:
        log_dir = Path(log_dir)

    log_dir.mkdir(parents=True, exist_ok=True)

    # Create default logger
    default_logger = get_logger(
        name="llmXive",
        log_file=log_dir / "app.log",
        metrics_file=metrics_file,
        level=level,
        json_format=json_format
    )

    _loggers["default"] = default_logger
    _metrics_handler = None
    for handler in default_logger.handlers:
        if isinstance(handler, MetricsHandler):
            _metrics_handler = handler
            break


def get_default_logger() -> logging.Logger:
    """Get the default project logger."""
    global _loggers
    if "default" not in _loggers:
        setup_default_loggers()
    return _loggers["default"]


# Convenience functions using default logger
def info(msg: str, **kwargs) -> None:
    """Log info message."""
    get_default_logger().info(msg, **kwargs)


def debug(msg: str, **kwargs) -> None:
    """Log debug message."""
    get_default_logger().debug(msg, **kwargs)


def warning(msg: str, **kwargs) -> None:
    """Log warning message."""
    get_default_logger().warning(msg, **kwargs)


def error(msg: str, **kwargs) -> None:
    """Log error message."""
    get_default_logger().error(msg, **kwargs)


def critical(msg: str, **kwargs) -> None:
    """Log critical message."""
    get_default_logger().critical(msg, **kwargs)
