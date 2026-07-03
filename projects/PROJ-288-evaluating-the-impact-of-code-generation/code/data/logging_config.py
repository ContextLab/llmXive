import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Ensure the logs directory exists
LOG_DIR = Path(__file__).parent.parent.parent / "data"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "run_logs.txt"

def setup_logging(
    log_file: Optional[Path] = None,
    level: int = logging.INFO,
    console_output: bool = True
) -> logging.Logger:
    """
    Configure the project logging infrastructure.

    This function sets up a logger that outputs to both a file and the console.
    It is designed to be called once at the start of the application.

    Args:
        log_file: Path to the log file. Defaults to data/run_logs.txt.
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
        console_output: If True, also log to stdout.

    Returns:
        The configured root logger for the project.
    """
    if log_file is None:
        log_file = LOG_FILE

    # Ensure the directory for the log file exists
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Get the root logger
    logger = logging.getLogger("llmXive")
    logger.setLevel(level)

    # Clear any existing handlers to prevent duplicate logs if called multiple times
    if logger.hasHandlers():
        logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File Handler
    try:
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        # Fallback if file cannot be opened
        print(f"Warning: Could not open log file {log_file}: {e}", file=sys.stderr)

    # Console Handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # Prevent propagation to the root Python logger to avoid double logging
    logger.propagate = False

    return logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieve a logger instance.

    If called without arguments, returns the configured project logger.
    If called with a name, returns a child logger.

    Args:
        name: Optional name for a child logger (e.g., 'data.fetch_prs').

    Returns:
        A logging.Logger instance.
    """
    if name is None:
        return logging.getLogger("llmXive")
    return logging.getLogger(f"llmXive.{name}")
