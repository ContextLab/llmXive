import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

class JsonFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_data["exc_info"] = self.formatException(record.exc_info)

        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)  # type: ignore

        return json.dumps(log_data)

def setup_logging(
    log_file: Optional[Path] = None,
    level: int = logging.INFO,
    console: bool = True,
) -> logging.Logger:
    """
    Configure root logger with JSON formatting for both file and stdout.

    Args:
        log_file: Optional path to write log file.
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
        console: Whether to log to stdout.

    Returns:
        The configured root logger.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # JSON Formatter
    json_formatter = JsonFormatter()

    if console:
        # Console handler (stdout)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(json_formatter)
        console_handler.setLevel(level)
        root_logger.addHandler(console_handler)

    if log_file is not None:
        # Ensure directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(json_formatter)
        file_handler.setLevel(level)
        root_logger.addHandler(file_handler)

    return root_logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.

    Args:
        name: Logger name (typically __name__ of the module).

    Returns:
        A configured logger instance.
    """
    return logging.getLogger(name)

def init_default_logger() -> logging.Logger:
    """
    Initialize a default logger for the project root if not already configured.
    Creates a 'logs' directory in the project root if needed.

    Returns:
        The default logger instance.
    """
    project_root = Path(__file__).resolve().parents[2]
    log_dir = project_root / "logs"
    log_file = log_dir / "pipeline.log"

    # Only setup if root logger has no handlers (prevents re-config on imports)
    if not logging.getLogger().handlers:
        setup_logging(log_file=log_file, level=logging.INFO, console=True)

    return get_logger("llmxive")

# Convenience function for immediate use in scripts
logger = init_default_logger()