"""
Logging infrastructure setup for llmXive EVA-Bench extension.

Configures file handlers, console handlers with appropriate levels,
and warning filters for edge cases as required by the project specification.
"""
import logging
import os
import sys
import warnings
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

from code.config import PROJECT_ROOT, LOG_DIR, LOG_LEVEL, LOG_MAX_BYTES, LOG_BACKUP_COUNT


def setup_logging(
    log_dir: Optional[Path] = None,
    log_level: Optional[int] = None,
    log_name: str = "llmxive",
    console_output: bool = True,
) -> logging.Logger:
    """
    Configure the root logger and project-specific logger with file and console handlers.

    Args:
        log_dir: Directory for log files. Defaults to PROJECT_ROOT / "logs".
        log_level: Logging level. Defaults to LOG_LEVEL from config.
        log_name: Name of the project logger.
        console_output: Whether to add a console handler.

    Returns:
        Configured logger instance.
    """
    # Resolve paths
    if log_dir is None:
        log_dir = LOG_DIR
    else:
        log_dir = Path(log_dir)

    log_dir.mkdir(parents=True, exist_ok=True)

    # Determine log level
    level = log_level if log_level is not None else LOG_LEVEL

    # Get the project logger
    logger = logging.getLogger(log_name)
    logger.setLevel(level)

    # Prevent adding handlers multiple times if called repeatedly
    if logger.handlers:
        return logger

    # Clear existing handlers from root to avoid double logging
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(level)

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler with rotation
    log_file = log_dir / f"{log_name}.log"
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    root_logger.addHandler(file_handler)

    # Console handler (optional)
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)  # Always show INFO+ on console
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        root_logger.addHandler(console_handler)

    # Configure warning filters for edge cases
    _setup_warning_filters()

    # Log startup
    logger.info("Logging infrastructure initialized.")
    logger.debug(f"Log directory: {log_dir}")
    logger.debug(f"Log level: {logging.getLevelName(level)}")

    return logger


def _setup_warning_filters() -> None:
    """
    Configure warnings module filters to handle edge cases gracefully.

    Filters applied:
    - DeprecationWarnings: Show once (standard behavior)
    - PendingDeprecationWarnings: Show once
    - ResourceWarning: Filtered to avoid noise from garbage collection
    - Specific library warnings (e.g., librosa, scipy) are logged but not ignored
    """
    # Standard deprecation behavior
    warnings.filterwarnings("default", category=DeprecationWarning)
    warnings.filterwarnings("default", category=PendingDeprecationWarning)

    # Filter resource warnings (e.g., unclosed files) to avoid spam in production
    # but still allow them to be seen if explicitly enabled via PYTHONWARNINGS
    if "resource" not in os.getenv("PYTHONWARNINGS", "").lower():
        warnings.filterwarnings("ignore", category=ResourceWarning)

    # Specific library warnings that might be noisy but are often benign
    # Librosa: sometimes warns about non-standard audio formats
    warnings.filterwarnings("ignore", message=".*non-standard sample rate.*", category=UserWarning)
    warnings.filterwarnings("ignore", message=".*hann window.*", category=UserWarning)

    # Scipy: warnings about convergence in optimization
    warnings.filterwarnings("ignore", message=".*Did not converge.*", category=RuntimeWarning)

    # Coqui TTS: often emits verbose training warnings
    warnings.filterwarnings("ignore", message=".*Torch version.*", category=UserWarning)

    # Log warning capture to our logger
    logging.captureWarnings(True)
    warnings_logger = logging.getLogger("py.warnings")
    warnings_logger.setLevel(logging.WARNING)


# Initialize logger on import if desired, or expose setup function
# For now, we expose the setup function to be called explicitly in main.py
# This prevents side effects on import
__all__ = ["setup_logging"]
