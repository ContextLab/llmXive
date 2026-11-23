"""
Structured logging utilities for the llmXive GW Compression pipeline.

This module provides a centralized logging configuration that ensures consistent,
structured output across all pipeline stages. It supports:
- JSON-formatted logs for easy parsing
- Log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Contextual information (module, function, line number)
- Pipeline step tracking
"""

import logging
import sys
import json
from datetime import datetime
from typing import Optional, Dict, Any, Union
from pathlib import Path

# Constants
DEFAULT_LOG_LEVEL = logging.INFO
PIPELINE_LOGGER_NAME = "gw_compression_pipeline"

# Global logger instance
_logger: Optional[logging.Logger] = None
_handler: Optional[logging.Handler] = None


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured JSON logs.
    
    Includes timestamp, level, module, function, message, and optional context.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }
        
        # Add extra context if present
        if hasattr(record, "step"):
            log_data["step"] = record.step
        if hasattr(record, "event_id"):
            log_data["event_id"] = record.event_id
        if hasattr(record, "data_path"):
            log_data["data_path"] = str(record.data_path)
        if hasattr(record, "compression_method"):
            log_data["compression_method"] = record.compression_method
        if hasattr(record, "metric_name"):
            log_data["metric_name"] = record.metric_name
        if hasattr(record, "metric_value"):
            log_data["metric_value"] = record.metric_value
        
        # Include exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


def setup_logging(
    log_level: int = DEFAULT_LOG_LEVEL,
    log_file: Optional[Union[str, Path]] = None,
    json_format: bool = True,
) -> logging.Logger:
    """
    Configure and return the main pipeline logger.
    
    Args:
        log_level: Logging level (e.g., logging.DEBUG, logging.INFO)
        log_file: Optional path to a log file. If None, logs only to stdout.
        json_format: If True, use structured JSON formatting. If False, use human-readable.
        
    Returns:
        Configured logger instance
        
    Example:
        >>> logger = setup_logging(log_level=logging.DEBUG, log_file="pipeline.log")
        >>> logger.info("Starting pipeline", extra={"step": "data_download"})
    """
    global _logger, _handler
    
    if _logger is not None:
        return _logger
    
    _logger = logging.getLogger(PIPELINE_LOGGER_NAME)
    _logger.setLevel(log_level)
    
    # Prevent duplicate handlers if called multiple times
    if _logger.handlers:
        _logger.handlers.clear()
    
    # Create formatter
    if json_format:
        formatter: logging.Formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - [%(module)s:%(funcName)s:%(lineno)d] - %(message)s"
        )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    _logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        _logger.addHandler(file_handler)
    
    return _logger


def get_logger() -> logging.Logger:
    """
    Get the configured pipeline logger.
    
    Raises:
        RuntimeError: If setup_logging() has not been called yet.
        
    Returns:
        The configured logger instance.
    """
    global _logger
    if _logger is None:
        # Auto-initialize with defaults if not explicitly set
        _logger = setup_logging()
    return _logger


def log_step_start(step_name: str, **context: Any) -> None:
    """
    Log the start of a pipeline step.
    
    Args:
        step_name: Name of the pipeline step (e.g., "download", "inject", "compress")
        **context: Additional context variables to include in the log
    """
    logger = get_logger()
    extra = {"step": step_name}
    extra.update(context)
    logger.info(f"Step '{step_name}' started", extra=extra)


def log_step_complete(step_name: str, **context: Any) -> None:
    """
    Log the successful completion of a pipeline step.
    
    Args:
        step_name: Name of the pipeline step
        **context: Additional context variables (e.g., files_processed, duration)
    """
    logger = get_logger()
    extra = {"step": step_name}
    extra.update(context)
    logger.info(f"Step '{step_name}' completed successfully", extra=extra)


def log_step_error(step_name: str, error: Exception, **context: Any) -> None:
    """
    Log an error that occurred during a pipeline step.
    
    Args:
        step_name: Name of the pipeline step
        error: The exception that was raised
        **context: Additional context variables
    """
    logger = get_logger()
    extra = {"step": step_name}
    extra.update(context)
    logger.error(f"Step '{step_name}' failed with error: {str(error)}", exc_info=True, extra=extra)


def log_metric(
    metric_name: str,
    metric_value: float,
    step_name: Optional[str] = None,
    **context: Any,
) -> None:
    """
    Log a numeric metric value.
    
    Args:
        metric_name: Name of the metric (e.g., "snr", "mse", "bias")
        metric_value: The numeric value
        step_name: Optional associated pipeline step
        **context: Additional context variables
    """
    logger = get_logger()
    extra = {
        "metric_name": metric_name,
        "metric_value": metric_value,
    }
    if step_name:
        extra["step"] = step_name
    extra.update(context)
    logger.info(f"Metric '{metric_name}': {metric_value}", extra=extra)


def log_event_processed(
    event_id: str,
    status: str,
    **context: Any,
) -> None:
    """
    Log the processing status of a GW event.
    
    Args:
        event_id: The GW event identifier (e.g., "GW150914")
        status: Processing status (e.g., "success", "skipped", "failed")
        **context: Additional context (e.g., snr, compression_ratio)
    """
    logger = get_logger()
    extra = {
        "event_id": event_id,
        "status": status,
    }
    extra.update(context)
    logger.info(f"Event '{event_id}' processed: {status}", extra=extra)


# Convenience aliases for common log levels
debug = get_logger().debug
info = get_logger().info
warning = get_logger().warning
error = get_logger().error
critical = get_logger().critical
