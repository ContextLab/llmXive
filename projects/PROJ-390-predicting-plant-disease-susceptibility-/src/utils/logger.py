import logging
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import traceback

class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs log records as JSON lines.
    Includes timestamp, level, logger name, message, and optional extra context.
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

        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }

        if record.__dict__.get("extra_data"):
            log_data["data"] = record.__dict__["extra_data"]

        return json.dumps(log_data)

class PlainTextFormatter(logging.Formatter):
    """
    Custom formatter for human-readable plain text logs with ISO timestamps.
    """
    def format(self, record: logging.LogRecord) -> str:
        dt_str = datetime.fromtimestamp(record.created).isoformat()
        return f"[{dt_str}] {record.levelname:<8} {record.name:<20} {record.getMessage()}"

def get_logger(name: str, log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Retrieves or creates a logger with the specified name.
    Configures handlers for console (JSON or text based on env) and optional file.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    # Avoid adding handlers if they already exist (idempotent)
    if logger.handlers:
        return logger

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Check for environment variable to choose format, default to JSON for machine parsing
    use_json = (os.getenv("LOG_FORMAT", "json").lower() == "json")
    if use_json:
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(PlainTextFormatter())
    
    logger.addHandler(console_handler)

    # File Handler (if path provided)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(JSONFormatter()) # Files always get JSON for structured analysis
        logger.addHandler(file_handler)

    return logger

def log_error(logger: logging.Logger, message: str, exc: Optional[Exception] = None, **extra: Any) -> None:
    """Logs an error message with optional exception and extra data."""
    record = logger.makeRecord(
        logger.name, logging.ERROR, "", 0, message, (), exc
    )
    if extra:
        record.__dict__["extra_data"] = extra
    logger.handle(record)

def log_warning(logger: logging.Logger, message: str, **extra: Any) -> None:
    """Logs a warning message with optional extra data."""
    record = logger.makeRecord(
        logger.name, logging.WARNING, "", 0, message, (), None
    )
    if extra:
        record.__dict__["extra_data"] = extra
    logger.handle(record)

def log_info(logger: logging.Logger, message: str, **extra: Any) -> None:
    """Logs an info message with optional extra data."""
    record = logger.makeRecord(
        logger.name, logging.INFO, "", 0, message, (), None
    )
    if extra:
        record.__dict__["extra_data"] = extra
    logger.handle(record)

def log_debug(logger: logging.Logger, message: str, **extra: Any) -> None:
    """Logs a debug message with optional extra data."""
    record = logger.makeRecord(
        logger.name, logging.DEBUG, "", 0, message, (), None
    )
    if extra:
        record.__dict__["extra_data"] = extra
    logger.handle(record)

def setup_logging_for_task(task_name: str, base_log_dir: Optional[Path] = None) -> logging.Logger:
    """
    Sets up a dedicated logger for a specific task.
    Creates a log file in the base_log_dir (default: data/logs) named {task_name}.log.
    """
    if base_log_dir is None:
        base_log_dir = Path("data") / "logs"
    
    base_log_dir.mkdir(parents=True, exist_ok=True)
    log_file = base_log_dir / f"{task_name}.log"
    
    return get_logger(task_name, log_file=str(log_file), level=logging.DEBUG)

def close_logging():
    """
    Closes all handlers and removes them to ensure clean shutdown.
    Useful for testing or long-running pipelines that spawn many loggers.
    """
    for logger in logging.Logger.manager.loggerDict.values():
        if isinstance(logger, logging.Logger):
            for handler in list(logger.handlers):
                handler.close()
                logger.removeHandler(handler)
    logging.shutdown()

import os # Imported for environment check in get_logger
