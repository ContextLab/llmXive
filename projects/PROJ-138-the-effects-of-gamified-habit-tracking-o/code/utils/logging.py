"""
Logging configuration for the pipeline.
"""
import logging
import sys
import os
from datetime import datetime

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Setup a logger with file and console handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if logger.handlers:
        return logger
    
    # File handler
    log_file = os.path.join(LOG_DIR, f"{name}.log")
    fh = logging.FileHandler(log_file)
    fh.setLevel(level)
    
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger

def log_pipeline_stage(stage: str, status: str):
    """Log a pipeline stage status."""
    logger = setup_logger("pipeline")
    logger.info(f"Stage: {stage} - Status: {status}")

pipeline_logger = setup_logger("pipeline")

if __name__ == "__main__":
    log_pipeline_stage("test", "running")
