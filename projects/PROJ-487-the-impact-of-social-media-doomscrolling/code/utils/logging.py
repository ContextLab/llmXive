"""
Logging utility configuration.
Provides a standard logger setup for the project.
"""
import logging
import os
import sys
import json
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

# Project root
_project_root = Path(__file__).resolve().parent.parent.parent
_log_dir = _project_root / "logs"

class JSONFormatter(logging.Formatter):
    """Custom formatter to output logs in JSON format."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        if record.exc_info:
            log_obj["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    console: bool = True
) -> None:
    """
    Configures the root logger.
    
    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
        log_file: Path to the log file. If None, defaults to logs/app.log.
        console: Whether to log to console.
    """
    if log_file is None:
        _log_dir.mkdir(exist_ok=True)
        log_file = _log_dir / "app.log"
    
    # Ensure log directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # File Handler
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024, # 10MB
        backupCount=5
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(file_handler)

    # Console Handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        # Use a simpler format for console
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Gets a logger with the specified name.
    
    Args:
        name: Logger name (usually __name__).
        
    Returns:
        Configured logger instance.
    """
    return logging.getLogger(name)


def configure_root_logger() -> None:
    """Alias for setup_logging with defaults."""
    setup_logging()


def main():
    """Test the logging setup."""
    setup_logging()
    logger = get_logger(__name__)
    logger.info("Logging setup test successful.")
    logger.debug("This is a debug message.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")


if __name__ == "__main__":
    main()