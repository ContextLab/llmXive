import logging
import os
from pathlib import Path
from typing import Optional

from config import load_paths

def setup_logging(log_level: int = logging.INFO) -> None:
    """
    Sets up logging configuration.
    """
    paths = load_paths()
    log_dir = paths.get('logs_dir', Path('data/logs'))
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "pipeline.log"

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def get_logger(name: str) -> logging.Logger:
    """
    Gets a logger with the given name.
    """
    return logging.getLogger(name)
