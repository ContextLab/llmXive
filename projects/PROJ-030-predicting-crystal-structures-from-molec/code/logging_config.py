import logging
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union
from config import get_path_absolute, ensure_directory

class JSONFormatter(logging.Formatter):
    """
    Custom logging formatter that outputs structured JSON logs.
    Includes timestamp, level, logger name, message, and optional extra fields.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName if hasattr(record, 'funcName') else None,
            "line": record.linno,
        }

        # Include exception info if present
        if record.exc_info:
            log_data["exception"] = self.format_exception(record.exc_info)

        # Include extra fields if present
        if hasattr(record, 'extra'):
            if isinstance(record.extra, dict):
                for key, value in record.extra.items():
                    # Avoid collisions with standard fields
                    if key not in log_data:
                        log_data[key] = value

        return json.dumps(log_data)

    def format_exception(self, exc_info: tuple) -> Optional[Dict[str, Any]]:
        """Format exception info into a dictionary."""
        try:
            import traceback
            return {
                "type": exc_info[0].__name__,
                "message": str(exc_info[1]),
                "traceback": traceback.format_tb(exc_info[2])
            }
        except Exception:
            return None

def setup_logging(log_file: Optional[Union[str, Path]] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Configure the root logger to output structured JSON to both console and file.

    Args:
        log_file: Optional path to a log file. If None, logs only to console.
        level: Logging level (e., logging.INFO, logging.DEBUG).

    Returns:
        The root logger instance.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers to avoid duplicates
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Console Handler (JSON)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(console_handler)

    # File Handler (JSON) if path provided
    if log_file:
        log_path = Path(log_file)
        ensure_directory(log_path.parent)
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(level)
        file_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(file_handler)

    return root_logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    Ensures the logger uses the JSON formatter configured in setup_logging.

    Args:
        name: The name of the logger (usually __name__).

    Returns:
        A configured Logger instance.
    """
    return logging.getLogger(name)

def log_event(logger: logging.Logger, event_type: str, message: str, **kwargs) -> None:
    """
    Log an event with additional structured fields.

    Args:
        logger: The logger instance to use.
        event_type: A categorical type for the event (e., "INFO", "ERROR", "METRIC").
        message: The main log message.
        **kwargs: Additional key-value pairs to include in the JSON log.
    """
    extra_fields = {"event_type": event_type, **kwargs}
    logger.info(message, extra={"extra": extra_fields})

def main() -> None:
    """
    Main entry point to demonstrate logging setup.
    Creates the logs directory and writes a test log entry.
    """
    project_root = get_path_absolute(".")
    logs_dir = os.path.join(project_root, "logs")
    ensure_directory(logs_dir)
    log_file_path = os.path.join(logs_dir, "pipeline.log")

    # Setup logging
    setup_logging(log_file=log_file_path, level=logging.INFO)
    logger = get_logger("logging_config_demo")

    # Log a test event
    log_event(
        logger,
        event_type="INIT",
        message="Logging infrastructure initialized successfully.",
        project_root=project_root,
        log_file=log_file_path
    )

    # Simulate an error log
    try:
        raise ValueError("Test error for logging demonstration")
    except ValueError as e:
        log_event(
            logger,
            event_type="ERROR",
            message=f"Caught exception during demo: {str(e)}",
            exception_type=type(e).__name__
        )

    print(f"Logs written to: {log_file_path}")

if __name__ == "__main__":
    main()
