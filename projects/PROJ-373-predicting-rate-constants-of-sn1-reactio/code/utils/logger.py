import logging
import sys
from pathlib import Path
from typing import Optional

def setup_logging(log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """Configure logging for the project."""
    logger = logging.getLogger("sn1_pipeline")
    logger.setLevel(level)

    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # File handler if specified
        if log_file:
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            logger.addHandler(fh)

    return logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name if name else "sn1_pipeline")
