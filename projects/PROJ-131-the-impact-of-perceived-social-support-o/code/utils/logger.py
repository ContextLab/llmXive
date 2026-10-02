"""
Logging infrastructure for the llmXive automated science pipeline.

This module initializes a logger that writes to `data/results/pipeline_run.log`.
All subsequent tasks (T012-T017) must use this logger to ensure consistent
logging across the pipeline.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

# Global logger instance
_logger: Optional[logging.Logger] = None

def setup_logging(log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Initialize the pipeline logger.

    Args:
        log_file: Path to the log file. Defaults to 'data/results/pipeline_run.log'.
        level: Logging level (e.g., logging.INFO, logging.DEBUG).

    Returns:
        The configured logger instance.

    Raises:
        RuntimeError: If the log directory cannot be created.
    """
    global _logger

    if _logger is not None:
        return _logger

    # Determine log file path
    if log_file is None:
        # Use project root relative path
        project_root = Path(__file__).parent.parent.parent
        log_file = project_root / "data" / "results" / "pipeline_run.log"
    else:
        log_file = Path(log_file)

    # Ensure log directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Create logger
    _logger = logging.getLogger("pipeline")
    _logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    _logger.handlers.clear()

    # Create file handler
    file_handler = logging.FileHandler(log_file, mode='w')
    file_handler.setLevel(level)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to logger
    _logger.addHandler(file_handler)
    _logger.addHandler(console_handler)

    _logger.info(f"Logging initialized. Log file: {log_file}")

    return _logger

def get_logger() -> logging.Logger:
    """
    Get the global logger instance.

    If the logger has not been initialized, this will raise a RuntimeError.
    Callers should ensure setup_logging() is called before get_logger().

    Returns:
        The configured logger instance.

    Raises:
        RuntimeError: If the logger has not been initialized.
    """
    global _logger
    if _logger is None:
        raise RuntimeError(
            "Logger not initialized. Call setup_logging() before get_logger()."
        )
    return _logger
