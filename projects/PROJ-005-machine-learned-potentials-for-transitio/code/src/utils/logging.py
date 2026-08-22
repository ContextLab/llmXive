import logging
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

class StructuredFormatter(logging.Formatter):
    """
    A custom logging formatter that outputs structured JSON logs.
    Includes timestamp, log level, module name, message, and optional extra context.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }

        # Include extra context if present
        if hasattr(record, 'extra_data'):
            log_entry['context'] = record.extra_data

        # Include exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_entry)

def setup_logger(
    name: str,
    level: int = logging.INFO,
    log_file: Optional[Union[str, Path]] = None,
    use_json: bool = True
) -> logging.Logger:
    """
    Sets up a logger with the specified name, level, and optional file output.

    Args:
        name: The name of the logger (typically __name__).
        level: The logging level (e.g., logging.DEBUG, logging.INFO).
        log_file: Optional path to a log file. If provided, logs are written to this file.
        use_json: If True, logs are formatted as JSON using StructuredFormatter.
                  If False, uses the default logging format.

    Returns:
        A configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent duplicate handlers if setup_logger is called multiple times
    if logger.handlers:
        return logger

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = StructuredFormatter() if use_json else logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(level)
        file_handler.setFormatter(console_formatter)
        logger.addHandler(file_handler)

    return logger

def log_progress(
    logger: logging.Logger,
    current: int,
    total: int,
    step_name: str,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Logs progress information in a structured way.

    Args:
        logger: The logger instance to use.
        current: The current progress count.
        total: The total count.
        step_name: A descriptive name for the current step.
        details: Optional dictionary of additional context (e.g., ETA, current item).
    """
    percentage = (current / total) * 100 if total > 0 else 0
    message = f"Progress: {current}/{total} ({percentage:.2f}%) - {step_name}"
    extra = details or {}
    extra['current'] = current
    extra['total'] = total
    extra['percentage'] = percentage
    extra['step'] = step_name

    logger.info(message, extra={'extra_data': extra})

def log_metric(
    logger: logging.Logger,
    metric_name: str,
    value: float,
    step: Optional[int] = None,
    epoch: Optional[int] = None,
    extra_tags: Optional[Dict[str, Any]] = None
) -> None:
    """
    Logs a metric value in a structured way.

    Args:
        logger: The logger instance to use.
        metric_name: The name of the metric (e.g., "loss", "accuracy").
        value: The numeric value of the metric.
        step: Optional global step number.
        epoch: Optional epoch number.
        extra_tags: Optional dictionary of additional tags or context.
    """
    message = f"Metric: {metric_name} = {value}"
    extra = extra_tags or {}
    extra['metric_name'] = metric_name
    extra['metric_value'] = value
    if step is not None:
        extra['step'] = step
    if epoch is not None:
        extra['epoch'] = epoch

    logger.info(message, extra={'extra_data': extra})

def log_error_summary(
    logger: logging.Logger,
    error_type: str,
    error_message: str,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Logs a structured error summary.

    Args:
        logger: The logger instance to use.
        error_type: The type or category of the error (e.g., "ValueError", "DataError").
        error_message: A human-readable description of the error.
        context: Optional dictionary of context information relevant to the error.
    """
    message = f"Error: [{error_type}] {error_message}"
    extra = context or {}
    extra['error_type'] = error_type
    extra['error_message'] = error_message

    logger.error(message, extra={'extra_data': extra})

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieves a logger instance. If a name is not provided, returns the root logger.

    Args:
        name: Optional name of the logger.

    Returns:
        A logging.Logger instance.
    """
    if name:
        return logging.getLogger(name)
    return logging.getLogger()
