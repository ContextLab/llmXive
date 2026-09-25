import logging
import os
import sys
from pathlib import Path
from config import LOGS_DIR

# Ensure log directory exists
LOGS_DIR.mkdir(parents=True, exist_ok=True)

class DetailedFormatter(logging.Formatter):
    """Custom formatter for detailed logging output."""
    def format(self, record):
        log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        self._style._fmt = log_fmt
        return super().format(record)

def setup_logger(name, log_file=None, level=logging.INFO):
    """
    Set up a logger with file and/or console handlers.
    
    Args:
        name: Logger name
        log_file: Path to log file (optional)
        level: Logging level
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()
    
    # Create formatter
    formatter = DetailedFormatter()
    
    # File handler if log_file specified
    if log_file:
        # Ensure directory exists
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    return logger

def get_logger(name):
    """Get an existing logger or create a new one with default settings."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger

def initialize_pipeline_logging():
    """Initialize logging infrastructure for the entire pipeline."""
    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove any existing handlers
    if root_logger.handlers:
        root_logger.handlers.clear()
    
    # Create console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(DetailedFormatter())
    root_logger.addHandler(ch)
    
    # Create file handler for general pipeline logs
    pipeline_log = LOGS_DIR / "pipeline.log"
    fh = logging.FileHandler(pipeline_log)
    fh.setFormatter(DetailedFormatter())
    root_logger.addHandler(fh)
    
    return root_logger

def get_preprocess_logger():
    """Get the logger for preprocessing tasks."""
    log_file = LOGS_DIR / "preprocess.log"
    return setup_logger("preprocess", log_file)

def get_download_logger():
    """Get the logger for download tasks."""
    log_file = LOGS_DIR / "download.log"
    return setup_logger("download", log_file)

def get_train_logger():
    """Get the logger for training tasks."""
    log_file = LOGS_DIR / "train.log"
    return setup_logger("train", log_file)

def get_project_logger():
    """Get the logger for project-wide tasks."""
    log_file = LOGS_DIR / "project.log"
    return setup_logger("project", log_file)

def get_evaluate_logger():
    """Get the logger for evaluation tasks."""
    log_file = LOGS_DIR / "evaluate.log"
    return setup_logger("evaluate", log_file)

def get_pipeline_logger():
    """Get the general pipeline logger."""
    log_file = LOGS_DIR / "pipeline.log"
    return setup_logger("pipeline", log_file)

# Initialize pipeline logging on module import
initialize_pipeline_logging()
