"""
Structured logging utilities for the calibration evaluation pipeline.

Provides configuration for JSON-formatted or console-formatted logs,
ensuring consistent log levels, timestamps, and contextual information
across the research pipeline.
"""

import logging
import sys
import json
from datetime import datetime
from typing import Optional, Dict, Any

# Global logger registry to avoid re-configuration
_configured = False
_log_level = logging.INFO

class StructuredFormatter(logging.Formatter):
    """
    A custom formatter that outputs logs as JSON lines for structured parsing.
    Includes timestamp, level, logger name, message, and optional extra fields.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        return json.dumps(log_data)

class ConsoleFormatter(logging.Formatter):
    """
    A human-readable formatter for console output with color codes.
    """

    COLORS = {
        logging.DEBUG: "\033[36m",    # Cyan
        logging.INFO: "\033[32m",     # Green
        logging.WARNING: "\033[33m",  # Yellow
        logging.ERROR: "\033[31m",    # Red
        logging.CRITICAL: "\033[35m", # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelno, self.RESET)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return (
            f"{color}[{timestamp}] {record.levelname:8} "
            f"{record.name:20} {record.message}{self.RESET}"
        )

def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    json_format: bool = False,
) -> None:
    """
    Configure the root logger for the application.

    Args:
        log_level: Logging level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Optional path to a log file. If provided, logs are written there.
        json_format: If True, use structured JSON formatting. Otherwise, use console formatting.
    """
    global _configured, _log_level

    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    if log_level.upper() not in level_map:
        raise ValueError(f"Invalid log level: {log_level}")

    _log_level = level_map[log_level.upper()]
    _configured = True

    root_logger = logging.getLogger()
    root_logger.setLevel(_log_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(_log_level)
    console_handler.setFormatter(
        StructuredFormatter() if json_format else ConsoleFormatter()
    )
    root_logger.addHandler(console_handler)

    # File Handler (if requested)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(_log_level)
        # File logs are always JSON for easier parsing by external tools
        file_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(file_handler)

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieve a logger instance.

    Args:
        name: Logger name. If None, returns the root logger.

    Returns:
        A configured logger instance.
    """
    logger_name = name if name else "llmXive.calibration"
    return logging.getLogger(logger_name)

def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    **context: Any,
) -> None:
    """
    Log a message with additional context fields.

    Args:
        logger: The logger instance to use.
        level: The logging level.
        message: The log message.
        **context: Key-value pairs to include in the structured log.
    """
    record = logger.makeRecord(
        logger.name,
        level,
        "",
        0,
        message,
        (),
        None,
    )
    record.extra_data = context  # type: ignore
    logger.handle(record)
