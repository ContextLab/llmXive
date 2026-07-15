"""
Logging infrastructure for the llmXive pipeline.

Provides structured logging with consistent formatting, log levels, and
context injection for pipeline stages. Ensures "fail loudly" behavior
by configuring handlers to output clear error messages on failure.
"""
import logging
import sys
import json
from datetime import datetime
from typing import Optional, Dict, Any, Union
from pathlib import Path

# Default log configuration
_logger: Optional[logging.Logger] = None
_handler: Optional[logging.Handler] = None
_structured_formatter: Optional[logging.Formatter] = None

# Log levels mapping
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL,
}

def get_logger(name: str = "llmxive") -> logging.Logger:
    """
    Get or create a logger with the specified name.
    
    Args:
        name: Logger name, typically the module name (__name__)
        
    Returns:
        Configured logger instance
    """
    global _logger, _handler, _structured_formatter
    
    if _logger is None:
        _logger = logging.getLogger(name)
        _logger.setLevel(logging.INFO)
        
        # Prevent adding multiple handlers if called multiple times
        if not _logger.handlers:
            _handler = logging.StreamHandler(sys.stdout)
            _handler.setLevel(logging.INFO)
            
            # Structured JSON formatter for pipeline stages
            _structured_formatter = StructuredFormatter()
            _handler.setFormatter(_structured_formatter)
            _logger.addHandler(_handler)
    
    # Set specific logger name for this instance
    logger = logging.getLogger(name)
    logger.setLevel(_logger.level)
    
    # Ensure handlers are attached if this is a child logger
    if not logger.handlers and _handler is not None:
        logger.addHandler(_handler)
        logger.propagate = False
    
    return logger

class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured JSON logs.
    
    Includes timestamp, level, logger name, message, and any
    additional context fields passed via extra dict.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra context if present
        if hasattr(record, "context") and record.context:
            log_entry["context"] = record.context
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry)

def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[Union[str, Path]] = None,
    enable_console: bool = True,
    enable_file: bool = False,
) -> logging.Logger:
    """
    Initialize logging infrastructure with specified configuration.
    
    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        enable_console: Whether to log to console (stdout)
        enable_file: Whether to log to file
        
    Returns:
        Root logger instance
    """
    global _logger, _handler, _structured_formatter
    
    if _logger is not None:
        # Logger already initialized, just update level if needed
        _logger.setLevel(LOG_LEVELS.get(log_level, logging.INFO))
        return _logger
    
    _logger = logging.getLogger("llmxive")
    _logger.setLevel(LOG_LEVELS.get(log_level, logging.INFO))
    
    # Clear any existing handlers
    _logger.handlers.clear()
    
    formatter = StructuredFormatter()
    
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(LOG_LEVELS.get(log_level, logging.INFO))
        console_handler.setFormatter(formatter)
        _logger.addHandler(console_handler)
    
    if enable_file and log_file:
        file_path = Path(log_file)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(file_path)
        file_handler.setLevel(LOG_LEVELS.get(log_level, logging.INFO))
        file_handler.setFormatter(formatter)
        _logger.addHandler(file_handler)
    
    _handler = _logger.handlers[0] if _logger.handlers else None
    _structured_formatter = formatter
    
    return _logger

def log_stage_start(
    logger: logging.Logger,
    stage_name: str,
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log the start of a pipeline stage with structured context.
    
    Args:
        logger: Logger instance to use
        stage_name: Name of the pipeline stage
        context: Optional dictionary of stage context parameters
    """
    extra = {"context": {"stage": stage_name, **(context or {})}}
    logger.info(f"Starting pipeline stage: {stage_name}", extra=extra)

def log_stage_complete(
    logger: logging.Logger,
    stage_name: str,
    duration_seconds: Optional[float] = None,
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log the successful completion of a pipeline stage.
    
    Args:
        logger: Logger instance to use
        stage_name: Name of the pipeline stage
        duration_seconds: Optional duration of the stage in seconds
        context: Optional dictionary of stage context parameters
    """
    extra = {"context": {"stage": stage_name, "status": "complete"}}
    if duration_seconds is not None:
        extra["context"]["duration_seconds"] = duration_seconds
    if context:
        extra["context"].update(context)
    
    logger.info(f"Completed pipeline stage: {stage_name}", extra=extra)

def log_stage_error(
    logger: logging.Logger,
    stage_name: str,
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log a stage failure with error details (fail loudly).
    
    Args:
        logger: Logger instance to use
        stage_name: Name of the pipeline stage
        error: The exception that caused the failure
        context: Optional dictionary of stage context parameters
    """
    extra = {"context": {"stage": stage_name, "status": "failed"}}
    if context:
        extra["context"].update(context)
    
    logger.error(
        f"Pipeline stage failed: {stage_name} - {str(error)}",
        exc_info=True,
        extra=extra,
    )

def log_data_validation(
    logger: logging.Logger,
    data_type: str,
    count: int,
    validation_status: str,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log data validation results with structured details.
    
    Args:
        logger: Logger instance to use
        data_type: Type of data being validated
        count: Number of items validated
        validation_status: Status of validation (passed, failed, warning)
        details: Optional dictionary with validation details
    """
    extra = {
        "context": {
            "data_type": data_type,
            "count": count,
            "validation_status": validation_status,
        }
    }
    if details:
        extra["context"].update(details)
    
    level = logging.INFO if validation_status == "passed" else logging.WARNING
    logger.log(
        level,
        f"Data validation: {data_type} - {count} items - {validation_status}",
        extra=extra,
    )

def log_metric(
    logger: logging.Logger,
    metric_name: str,
    value: Union[int, float],
    stage: Optional[str] = None,
) -> None:
    """
    Log a computed metric with optional stage context.
    
    Args:
        logger: Logger instance to use
        metric_name: Name of the metric
        value: Metric value
        stage: Optional stage name where metric was computed
    """
    extra = {"context": {"metric": metric_name, "value": value}}
    if stage:
        extra["context"]["stage"] = stage
    
    logger.info(f"Metric recorded: {metric_name} = {value}", extra=extra)

# Convenience function for quick logging setup
def configure_default_logging() -> logging.Logger:
    """
    Configure logging with default settings (INFO level, console output).
    
    Returns:
        Root logger instance
    """
    return setup_logging(
        log_level="INFO",
        enable_console=True,
        enable_file=False,
    )