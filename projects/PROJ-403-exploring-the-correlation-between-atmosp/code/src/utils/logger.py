import logging
import os
import sys
from pathlib import Path
from typing import Optional

def setup_logging(log_level: Optional[str] = None, log_file: Optional[str] = None) -> logging.Logger:
    """Configure logging for the application."""
    logger = logging.getLogger("llmXive")
    if not logger.handlers:
        logger.setLevel(getattr(logging, log_level.upper() if log_level else "INFO"))

        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # File handler if specified
        if log_file:
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
            fh = logging.FileHandler(log_file)
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(formatter)
            logger.addHandler(fh)

    return logger

def get_logger(name: str = "llmXive") -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)
