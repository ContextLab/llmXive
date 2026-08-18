import logging
import os
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional
import json
from datetime import datetime

# Global logger instance
_logger: Optional[logging.Logger] = None

def setup_logging(log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """Configure the root logger with file and console handlers."""
    global _logger
    if _logger is not None:
        return _logger

    logger = logging.getLogger("pipeline")
    logger.setLevel(level)

    # Clear existing handlers
    logger.handlers.clear()

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console Handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File Handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        fh = RotatingFileHandler(log_path, maxBytes=5*1024*1024, backupCount=3)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    _logger = logger
    return logger

def get_logger() -> logging.Logger:
    """Get the configured logger, initializing if necessary."""
    global _logger
    if _logger is None:
        # Default to console only if not explicitly set up
        _logger = logging.getLogger("pipeline")
        _logger.setLevel(logging.INFO)
        if not _logger.handlers:
            ch = logging.StreamHandler(sys.stdout)
            ch.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            _logger.addHandler(ch)
    return _logger

def log_warning_structured(message: str, context: dict) -> None:
    """Log a structured warning message."""
    logger = get_logger()
    structured_msg = f"WARN: {message} | Context: {json.dumps(context)}"
    logger.warning(structured_msg)
