"""
Logging infrastructure for the pipeline.

Records event exclusion counts and pipeline steps.
"""
import logging
import sys
from pathlib import Path
from datetime import datetime

def setup_logger(
    name: str,
    log_file: str = "logs/pipeline.log",
    level: int = logging.INFO
) -> logging.Logger:
    """
    Setup a logger with file and console handlers.

    Args:
        name: Logger name
        log_file: Path to log file
        level: Logging level

    Returns:
        Configured logger instance
    """
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(level)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger

def log_event_exclusion(logger: logging.Logger, reason: str, count: int) -> None:
    """Log event exclusion details."""
    logger.warning(f"Excluded {count} events due to: {reason}")

def log_pipeline_step(logger: logging.Logger, step: str, details: str) -> None:
    """Log pipeline step completion."""
    logger.info(f"Step '{step}': {details}")
