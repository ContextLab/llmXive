"""
Structured logging setup for the pipeline.
"""
import logging
import sys
import os
from datetime import datetime

def setup_logger(name: str = "pipeline", level: int = logging.INFO):
    """Setup a standard logger."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    # File handler
    logs_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    log_file = os.path.join(logs_dir, f"{name}_{datetime.now().strftime('%Y%m%d')}.log")
    
    fh = logging.FileHandler(log_file)
    fh.setLevel(level)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    return logger

def log_pipeline_stage(logger: logging.Logger, stage: str, message: str):
    """Log a pipeline stage start or end."""
    logger.info(f"[{stage}] {message}")

pipeline_logger = setup_logger("pipeline")
