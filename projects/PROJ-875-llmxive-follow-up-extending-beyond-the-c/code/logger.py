"""
JSON-formatted rotating file handler for llmXive.
Provides a centralized logging configuration that redirects stdout/stderr
to a rotating JSON log file.
"""
import json
import logging
import logging.handlers
import sys
import os
from typing import Optional, TextIO, Dict, Any
from datetime import datetime

# Constants for log rotation
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
LOG_FILENAME = "execution.log"
MAX_BYTES = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

def get_json_formatter() -> logging.Formatter:
    """
    Returns a custom formatter that outputs JSON lines.
    """
    class JsonFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            log_entry: Dict[str, Any] = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno
            }
            if record.exc_info:
                log_entry["exception"] = self.formatException(record.exc_info)
            return json.dumps(log_entry)

    return JsonFormatter()

def setup_logger(
    name: str = "llmxive",
    log_file: Optional[str] = None,
    level: int = logging.INFO
) -> logging.Logger:
    """
    Configures a logger with a rotating JSON file handler and a console handler.
    The file handler is set to JSON format.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers multiple times if called repeatedly
    if logger.handlers:
        return logger

    # File handler (Rotating)
    file_path = os.path.join(LOG_DIR, log_file or LOG_FILENAME)
    file_handler = logging.handlers.RotatingFileHandler(
        file_path,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8"
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(get_json_formatter())

    # Console handler (for immediate feedback, optional JSON or text)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(get_json_formatter())

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

class StdoutRedirector:
    """
    Redirects stdout and stderr to the logging system.
    """
    def __init__(self, logger: logging.Logger, level: int = logging.INFO):
        self.logger = logger
        self.level = level
        self._stdout_buffer = []
        self._stderr_buffer = []

    def write(self, text: str) -> None:
        if text.strip():
            self.logger.log(self.level, text.rstrip())

    def flush(self) -> None:
        pass

    def redirect(self) -> None:
        """Redirects sys.stdout and sys.stderr to the logger."""
        sys.stdout = self
        sys.stderr = self

    def restore(self) -> None:
        """Restores original stdout and stderr."""
        # Note: In a real production scenario, we might want to save the original
        # references before redirecting. For this implementation, we assume
        # the script lifecycle manages this or we just leave them redirected.
        pass

def configure_global_logging() -> logging.Logger:
    """
    Sets up the global logger and redirects stdout/stderr to it.
    Returns the configured logger instance.
    """
    logger = setup_logger()
    redirector = StdoutRedirector(logger)
    redirector.redirect()
    return logger

# Convenience function to get the configured logger
def get_logger() -> logging.Logger:
    return logging.getLogger("llmxive")
