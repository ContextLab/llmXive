import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
from config import get_project_root, get_processed_data_dir

# Global logger instance
_logger = None

def setup_logging(log_file: Optional[str] = None, level: int = logging.INFO):
    """
    Sets up the logging configuration for the pipeline.
    
    Args:
        log_file: Optional path to a log file. If None, logs to data/pipeline.log.
        level: Logging level (default: INFO).
    """
    global _logger
    
    if _logger is not None:
        return _logger

    # Determine log file path
    if log_file is None:
        # Ensure we are writing to data/pipeline.log as per task requirement
        # get_processed_data_dir() points to data/processed, so we need to adjust
        # The task explicitly says: "write logs to data/pipeline.log"
        project_root = get_project_root()
        log_dir = project_root / "data"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "pipeline.log"
    
    # Create logger
    logger = logging.getLogger("llmXive")
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    _logger = logger
    
    # Log startup message to verify file creation
    logger.info("Logging infrastructure initialized. Pipeline log started.")
    
    return logger

def get_logger():
    """Returns the configured logger instance."""
    if _logger is None:
        setup_logging()
    return _logger

def log_pipeline_step(step_name: str, details: Optional[str] = None):
    """Logs a pipeline step start or completion."""
    logger = get_logger()
    msg = f"PIPELINE STEP: {step_name}"
    if details:
        msg += f" - {details}"
    logger.info(msg)

def log_exclusion(reason: str, participant_id: Optional[str] = None, stimulus_id: Optional[str] = None):
    """Logs an exclusion event."""
    logger = get_logger()
    msg = f"EXCLUSION: {reason}"
    if participant_id:
        msg += f" [Participant: {participant_id}]"
    if stimulus_id:
        msg += f" [Stimulus: {stimulus_id}]"
    logger.warning(msg)