import os
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

# Ensure the logs directory exists
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "pipeline.log"

class PipelineFormatter(logging.Formatter):
    """Custom formatter for pipeline logs with timestamp and level."""
    def format(self, record):
        # Add specific context for exclusion reasons if present
        if hasattr(record, 'exclusion_reason'):
            record.msg = f"[EXCLUSION] {record.exclusion_reason}: {record.msg}"
        return super().format(record)

def get_logger(name: str = "pipeline") -> logging.Logger:
    """
    Get or create a logger configured to write to logs/pipeline.log.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times if called repeatedly
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # File handler for persistent logs
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(PipelineFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    
    # Console handler for immediate feedback
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(PipelineFormatter(
        '%(levelname)s: %(message)s'
    ))
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def log_exclusion_reason(reason: str, details: Optional[str] = None, logger_name: str = "pipeline"):
    """
    Log a specific exclusion reason for a data point.
    
    Args:
        reason: The primary reason for exclusion (e.g., 'Missing Ionic Radius')
        details: Optional additional context
        logger_name: Name of the logger to use
    """
    logger = get_logger(logger_name)
    extra = {'exclusion_reason': reason}
    if details:
        logger.warning(f"{reason}: {details}", extra=extra, exc_info=False)
    else:
        logger.warning(reason, extra=extra, exc_info=False)

def log_pipeline_event(event: str, level: int = logging.INFO, logger_name: str = "pipeline"):
    """
    Log a general pipeline event.
    
    Args:
        event: Description of the event
        level: Logging level (default INFO)
        logger_name: Name of the logger to use
    """
    logger = get_logger(logger_name)
    logger.log(level, event)

# Initialize root logger configuration if needed
def initialize_logging():
    """Initialize logging infrastructure."""
    logger = get_logger()
    log_pipeline_event("Logging infrastructure initialized", logging.INFO)
    log_pipeline_event(f"Log file location: {LOG_FILE.absolute()}", logging.INFO)

if __name__ == "__main__":
    initialize_logging()
    logger = get_logger()
    log_pipeline_event("Testing logging infrastructure")
    log_exclusion_reason("Test Exclusion", "This is a test exclusion reason")
    log_pipeline_event("Logging test completed", logging.INFO)
