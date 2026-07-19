import logging
import sys
import os
import traceback
from typing import Optional, Dict, Any
from pathlib import Path

def setup_logging(log_level=logging.INFO):
    """Sets up basic logging configuration."""
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )

def get_logger(name: str) -> logging.Logger:
    """Returns a logger with the given name."""
    return logging.getLogger(name)

def log_exception(logger, exc: Optional[Exception] = None):
    """Logs an exception with traceback information."""
    if exc:
        logger.error("An unhandled exception occurred:", exc_info=True)
    else:
      logger.warning("Log Exception called without exception object.")
