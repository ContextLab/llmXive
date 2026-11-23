"""
Logging utilities for the llmXive pipeline.
Provides JSON-formatted logging, file and stdout handlers, and logger initialization.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any


class JsonFormatter(logging.Formatter):
    """Custom formatter that outputs log records as JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            log_data.update(record.extra_data)

        return json.dumps(log_data)


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
    json_format: bool = True,
) -> logging.Logger:
    """
    Configure the root logger with handlers for stdout and optional file output.

    Args:
        log_level: Logging level (e.g., "DEBUG", "INFO", "WARNING", "ERROR").
        log_file: Optional path to write log output.
        json_format: If True, use JSON formatting; otherwise use standard format.

    Returns:
        The root logger instance.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    formatter: logging.Formatter
    if json_format:
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name: Logger name (typically __name__ of the module).

    Returns:
        A configured logger instance.
    """
    return logging.getLogger(name)


def init_default_logger(log_dir: Optional[Path] = None) -> logging.Logger:
    """
    Initialize a default logger with file output in the specified directory.

    Args:
        log_dir: Directory to store log files. Defaults to 'logs' in current dir.

    Returns:
        A configured logger instance.
    """
    if log_dir is None:
        log_dir = Path.cwd() / "logs"

    log_file = log_dir / f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    setup_logging(log_level="INFO", log_file=log_file, json_format=True)
    return get_logger(__name__)
