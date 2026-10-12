import logging
import os
from pathlib import Path
from typing import Optional

def setup_logging(log_file: Optional[str] = "logs/run.log") -> logging.Logger:
    """
    Standard logging setup used by multiple scripts.
    Creates the log directory if it doesn't exist.
    """
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("llmxive")

def setup_project_logging() -> logging.Logger:
    """
    Alias for setup_logging to satisfy imports in 01_data_curation.py.
    """
    return setup_logging()

def get_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """
    Get a named logger. If log_file is provided, it re-configures the handler.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        if log_file:
            path = Path(log_file)
            path.parent.mkdir(parents=True, exist_ok=True)
            handler = logging.FileHandler(path)
            handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            logger.addHandler(handler)
        
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(stream_handler)
        
    logger.setLevel(logging.INFO)
    return logger
