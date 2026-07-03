"""
Structured logging configuration for the research pipeline.
"""
import logging
import sys
import os
from datetime import datetime

def setup_logger(name: str, log_file: str = None, level: int = logging.INFO) -> logging.Logger:
    """
    Setup a structured logger with console and optional file handlers.
    
    Args:
        name: Name of the logger (usually __name__).
        log_file: Path to log file. If None, only console output is used.
        level: Logging level.
        
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding handlers if already present (prevents duplicate logs in tests)
    if logger.handlers:
        return logger
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        # Ensure directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# Pre-configured logger for general pipeline use
pipeline_logger = setup_logger("llmXive_pipeline", "logs/pipeline.log")

def log_pipeline_stage(stage_name: str, status: str, details: dict = None):
    """
    Log a structured message for a specific pipeline stage.
    
    Args:
        stage_name: Name of the pipeline stage (e.g., 'Data Ingestion', 'Model Training').
        status: Status of the stage (e.g., 'STARTED', 'COMPLETED', 'FAILED').
        details: Optional dictionary of additional context (e.g., record counts, timing).
    """
    msg = f"STAGE: {stage_name} | STATUS: {status}"
    if details:
        detail_str = ", ".join(f"{k}={v}" for k, v in details.items())
        msg += f" | DETAILS: {detail_str}"
    
    if status == "FAILED":
        pipeline_logger.error(msg)
    elif status == "COMPLETED":
        pipeline_logger.info(msg)
    elif status == "STARTED":
        pipeline_logger.info(msg)
    else:
        pipeline_logger.debug(msg)