import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from config import get_logs_root, get_project_root

# Global logger instance
_logger: Optional[logging.Logger] = None
_handler: Optional[logging.Handler] = None

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
JSON_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


class StructuredJsonFormatter(logging.Formatter):
    """
    A custom formatter that outputs log records as structured JSON.
    Includes timestamp, level, logger name, message, and optional extra fields.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add standard attributes
        if hasattr(record, "filename"):
            log_data["filename"] = record.filename
        if hasattr(record, "lineno"):
            log_data["lineno"] = record.lineno
        if hasattr(record, "funcName"):
            log_data["funcName"] = record.funcName

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "__dict__"):
            for key, value in record.__dict__.items():
                if key not in {"msg", "args", "levelname", "levelno",
                               "pathname", "filename", "module",
                               "lineno", "funcName", "created",
                               "msecs", "relativeCreated", "thread",
                               "threadName", "processName", "process",
                               "message", "exc_info", "exc_text",
                               "stack_info", "name"}:
                    log_data[key] = value

        return json.dumps(log_data)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieves or creates the project logger with structured JSON output.
    If name is None, uses the project root name.
    """
    global _logger, _handler

    if _logger is None:
        _logger = logging.getLogger("llmXive")
        _logger.setLevel(logging.DEBUG)

        # Prevent adding multiple handlers if called multiple times
        if not _logger.handlers:
            # Ensure logs directory exists
            logs_root = get_logs_root()
            logs_root.mkdir(parents=True, exist_ok=True)

            # Console handler (optional, for immediate feedback)
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
            _logger.addHandler(console_handler)

            # File handler with JSON formatting
            log_file = logs_root / "pipeline.log"
            file_handler = logging.FileHandler(log_file, mode="a")
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(StructuredJsonFormatter())
            _logger.addHandler(file_handler)

    if name:
        return _logger.getChild(name)
    return _logger


def setup_logging(name: Optional[str] = None) -> logging.Logger:
    """
    Alias for get_logger to explicitly set up logging infrastructure.
    """
    return get_logger(name)
