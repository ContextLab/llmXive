import os
import logging
import sys
from pathlib import Path
from typing import Optional

def setup_logging():
    """Configure logging to file and console."""
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "pipeline.log"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)

def raise_on_missing_data(message: str):
    """Raise ValueError if data is missing."""
    raise ValueError(message)
