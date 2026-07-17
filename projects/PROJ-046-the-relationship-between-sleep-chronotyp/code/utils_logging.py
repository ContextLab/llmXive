"""
Logging Utilities for PROJ-046

Provides centralized logging configuration, loggers, and helper functions
for the entire pipeline.
"""
import logging
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Singleton logger instance
_pipeline_logger: Optional[logging.Logger] = None


def get_project_root() -> Path:
    """Get the project root directory."""
    # Assumes code/ is at the root level or one level deep
    current_file = Path(__file__).resolve()
    if current_file.name == "utils_logging.py":
        # If in code/
        return current_file.parent.parent
    else:
        return current_file.parent


def ensure_log_directory() -> Path:
    """Ensure the logs directory exists."""
    root = get_project_root()
    logs_dir = root / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def setup_logger(name: str = "pipeline") -> logging.Logger:
    """
    Setup and return a logger with file and console handlers.
    
    Args:
        name: Name for the logger.
        
    Returns:
        Configured logger instance.
    """
    global _pipeline_logger
    
    if _pipeline_logger is not None:
        return _pipeline_logger
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        _pipeline_logger = logger
        return logger
    
    logs_dir = ensure_log_directory()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"{name}_{timestamp}.log"
    
    # File Handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        "%(levelname)s: %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    _pipeline_logger = logger
    return logger


def get_pipeline_logger() -> logging.Logger:
    """Get the main pipeline logger instance."""
    if _pipeline_logger is None:
        return setup_logger()
    return _pipeline_logger


def log_info(message: str) -> None:
    """Log an info message."""
    logger = get_pipeline_logger()
    logger.info(message)


def log_warning(message: str) -> None:
    """Log a warning message."""
    logger = get_pipeline_logger()
    logger.warning(message)


def log_error(message: str) -> None:
    """Log an error message."""
    logger = get_pipeline_logger()
    logger.error(message)


def log_abort(message: str) -> None:
    """Log an error and raise an exception to abort the pipeline."""
    logger = get_pipeline_logger()
    logger.error(f"ABORT: {message}")
    raise RuntimeError(f"Pipeline aborted: {message}")


def log_exclusion(reason: str, row_id: Optional[str] = None) -> None:
    """Log an exclusion event."""
    logger = get_pipeline_logger()
    msg = f"Exclusion: {reason}"
    if row_id:
        msg += f" (Row ID: {row_id})"
    logger.warning(msg)
    
    # Also write to specific exclusion log if needed
    logs_dir = ensure_log_directory()
    exclusion_log = logs_dir / "exclusions.log"
    with open(exclusion_log, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()} - {msg}\n")


def log_exclusion_count(count: int, step: str) -> None:
    """Log a summary of exclusion counts."""
    logger = get_pipeline_logger()
    logger.info(f"Exclusion Summary ({step}): {count} rows excluded.")


def check_log_file_exists(filename: str) -> bool:
    """Check if a specific log file exists."""
    logs_dir = ensure_log_directory()
    return (logs_dir / filename).exists()


def read_log_file(filename: str) -> str:
    """Read the content of a log file."""
    logs_dir = ensure_log_directory()
    file_path = logs_dir / filename
    if not file_path.exists():
        raise FileNotFoundError(f"Log file not found: {file_path}")
    return file_path.read_text(encoding="utf-8")
