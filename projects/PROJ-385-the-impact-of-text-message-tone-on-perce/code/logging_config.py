import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
from config import get_project_root, get_processed_data_dir

def setup_logging() -> logging.Logger:
    """
    Configures and returns a logger instance.
    Writes to data/pipeline.log as per task requirement.
    
    Returns:
        logging.Logger: Configured logger.
    """
    logger = logging.getLogger('pipeline')
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        # Determine the log file path: data/pipeline.log relative to project root
        project_root = get_project_root()
        log_file = project_root / "data" / "pipeline.log"
        
        # Ensure the data directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # File handler
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)
        
        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)

    return logger

def get_logger() -> logging.Logger:
    """Returns the configured logger."""
    return setup_logging()

def log_pipeline_step(step_name: str) -> None:
    """Logs a pipeline step."""
    logger = get_logger()
    logger.info(f"Pipeline Step: {step_name}")

def log_exclusion(reason: str, record_id: str) -> None:
    """Logs an exclusion reason."""
    logger = get_logger()
    logger.info(f"Exclusion: {reason} for record {record_id}")