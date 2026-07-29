import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

class JsonFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "extra_data"):
            log_obj.update(record.extra_data)

        return json.dumps(log_obj)


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
    enable_json: bool = True,
) -> None:
    """
    Configure root logger with stdout and optional file handlers.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Optional path to write logs. If None, no file handler is added.
        enable_json: If True, use JSON formatting; otherwise use standard text formatting.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Clear existing handlers to avoid duplicates in repeated calls
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))

    if enable_json:
        console_handler.setFormatter(JsonFormatter())
    else:
        console_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )
    root_logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        # Ensure directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        # File logs always use JSON for easier parsing
        file_handler.setFormatter(JsonFormatter())
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger configured with the root handlers.

    Args:
        name: Logger name (typically __name__).

    Returns:
        Configured logger instance.
    """
    return logging.getLogger(name)


def init_default_logger() -> logging.Logger:
    """
    Initialize and return a default logger with standard setup.

    Returns:
        Configured logger instance.
    """
    setup_logging(
        log_level="INFO",
        log_file=Path("logs") / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
        enable_json=True,
    )
    return get_logger("llmXive")