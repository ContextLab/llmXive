import logging
import os
import sys
from pathlib import Path
from typing import Optional

_logger: Optional[logging.Logger] = None

def setup_logging(
    log_level: int = logging.INFO,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Setup the root logger with console and optional file handlers.

    Args:
        log_level: Logging level (e.g., logging.DEBUG, logging.INFO).
        log_file: Optional path to a log file.

    Returns:
        The configured logger instance.
    """
    global _logger
    if _logger is not None:
        return _logger

    _logger = logging.getLogger("llmXive")
    _logger.setLevel(log_level)

    # Avoid adding handlers multiple times if called repeatedly
    if not _logger.handlers:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(log_level)
        ch.setFormatter(formatter)
        _logger.addHandler(ch)

        # File handler (optional)
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            fh = logging.FileHandler(log_file)
            fh.setLevel(log_level)
            fh.setFormatter(formatter)
            _logger.addHandler(fh)

    return _logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance, optionally named.

    Args:
        name: Name for the logger (e.g., __name__).

    Returns:
        A configured logger instance.
    """
    if _logger is None:
        setup_logging()
    
    if name:
        return _logger.getChild(name)
    return _logger
