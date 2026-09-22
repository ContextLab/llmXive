import logging
import os
import sys
from pathlib import Path
from config import LOGS_DIR

class DetailedFormatter(logging.Formatter):
    """
    Custom formatter that includes timestamp, level, module name, and message.
    Designed for research pipelines to ensure reproducibility and traceability.
    """
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

def setup_logger(
    name: str,
    log_file: Path | None = None,
    level: int = logging.INFO,
    console: bool = True
) -> logging.Logger:
    """
    Configure a logger with optional file and console handlers.

    Args:
        name: Logger name (usually __name__)
        log_file: Path to log file (relative to LOGS_DIR if not absolute)
        level: Logging level (e.g., logging.DEBUG, logging.INFO)
        console: Whether to add a console handler

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    # Create formatter
    formatter = DetailedFormatter()

    # Console handler
    if console:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(level)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    # File handler
    if log_file:
        # Ensure log directory exists
        log_path = Path(log_file)
        if not log_path.is_absolute():
            log_path = LOGS_DIR / log_file
        
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        fh = logging.FileHandler(str(log_path))
        fh.setLevel(level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Retrieve an existing logger or create a default one if it doesn't exist.
    This ensures consistent logging configuration across the pipeline.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        # Default setup if not explicitly configured
        logger = setup_logger(name, log_file=f"{name}.log", level=logging.INFO)
    return logger

# Pre-configure common loggers for immediate use
# This ensures that downstream tasks can immediately write to logs/
# without needing to call setup_logger again for standard components.
_initialized = False

def initialize_pipeline_logging():
    """
    Initialize standard loggers for the pipeline components.
    Call this once at the start of the main execution script.
    """
    global _initialized
    if _initialized:
        return
    
    # Ensure LOGS_DIR exists
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Initialize standard loggers
    setup_logger("pipeline", log_file="pipeline.log", level=logging.INFO)
    setup_logger("download", log_file="download.log", level=logging.INFO)
    setup_logger("preprocess", log_file="preprocess.log", level=logging.INFO)
    setup_logger("train", log_file="train.log", level=logging.INFO)
    setup_logger("project", log_file="project.log", level=logging.INFO)
    setup_logger("evaluate", log_file="evaluate.log", level=logging.INFO)
    
    _initialized = True

def get_preprocess_logger() -> logging.Logger:
    """
    Get the specific logger for preprocessing tasks.
    Used by T013 to generate logs/preprocess_counts.yaml.
    
    Returns:
        Preprocess logger instance
    """
    return get_logger("preprocess")

def get_download_logger() -> logging.Logger:
    """
    Get the specific logger for download tasks.
    
    Returns:
        Download logger instance
    """
    return get_logger("download")

def get_train_logger() -> logging.Logger:
    """
    Get the specific logger for training tasks.
    
    Returns:
        Train logger instance
    """
    return get_logger("train")

def get_project_logger() -> logging.Logger:
    """
    Get the specific logger for projection tasks.
    
    Returns:
        Project logger instance
    """
    return get_logger("project")

def get_evaluate_logger() -> logging.Logger:
    """
    Get the specific logger for evaluation tasks.
    
    Returns:
        Evaluate logger instance
    """
    return get_logger("evaluate")

def get_pipeline_logger() -> logging.Logger:
    """
    Get the main pipeline logger.
    
    Returns:
        Pipeline logger instance
    """
    return get_logger("pipeline")