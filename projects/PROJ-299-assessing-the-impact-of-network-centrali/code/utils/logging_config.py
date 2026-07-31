import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Union

class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs machine-readable JSON log entries.
    Per FR-011: Logs must be machine-readable for pipeline monitoring.
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

        # Include exception info if present
        if record.exc_info:
            log_entry["exc_info"] = self.formatException(record.exc_info)

        # Include extra context if available
        if hasattr(record, "extra_data"):
            log_entry["data"] = record.extra_data

        return json.dumps(log_entry)

def setup_logging(
    log_file: Optional[Union[str, Path]] = None,
    level: int = logging.INFO,
    console_output: bool = True
) -> logging.Logger:
    """
    Initialize the logging infrastructure.

    Args:
        log_file: Path to the log file. If None, defaults to 'logs/pipeline.log'
                  relative to the project root.
        level: Logging level (e.g., logging.INFO, logging.DEBUG).
        console_output: If True, also log to stderr.

    Returns:
        The root logger configured for the pipeline.
    """
    # Determine log file path
    if log_file is None:
        project_root = Path(__file__).resolve().parent.parent.parent
        log_dir = project_root / "logs"
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / "pipeline.log"
    else:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(level)

    # Clear existing handlers to avoid duplicates in re-runs
    logger.handlers.clear()

    # File handler with JSON formatter
    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setLevel(level)
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)

    # Console handler (optional)
    if console_output:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(level)
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(console_handler)

    return logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance. If name is provided, returns a child logger.
    Otherwise returns the root logger.
    """
    if name:
        return logging.getLogger(name)
    return logging.getLogger()

def log_event(
    logger: logging.Logger,
    event_type: str,
    message: str,
    data: Optional[Dict[str, Any]] = None,
    level: int = logging.INFO
) -> None:
    """
    Log a structured event with optional data payload.

    Args:
        logger: The logger instance to use.
        event_type: Type of event (e.g., 'START', 'END', 'ERROR', 'METRIC').
        message: Human-readable description of the event.
        data: Optional dictionary of additional data to include in the log.
        level: Logging level.
    """
    extra = {"extra_data": {"event_type": event_type, **(data or {})}}
    logger.log(level, message, extra=extra)
