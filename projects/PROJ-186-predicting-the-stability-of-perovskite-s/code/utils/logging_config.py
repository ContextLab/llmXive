import os
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

# Ensure the logs directory exists
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE_PATH = LOG_DIR / "pipeline.log"
EXCLUSION_LOG_FILE_PATH = LOG_DIR / "exclusions.log"

# Create a custom formatter that includes timestamp, level, and message
class PipelineFormatter(logging.Formatter):
    def format(self, record):
        # Add custom fields if they exist
        if hasattr(record, 'exclusion_reason'):
            record.msg = f"[EXCLUSION] {record.exclusion_reason}: {record.msg}"
        return super().format(record)

# Configure the root logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Clear existing handlers to avoid duplicates in repeated runs
if logger.handlers:
    logger.handlers.clear()

# File handler for general pipeline events (Rotating to prevent huge files)
file_handler = RotatingFileHandler(
    LOG_FILE_PATH, maxBytes=10*1024*1024, backupCount=5
)
file_handler.setLevel(logging.INFO)
file_format = PipelineFormatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_format)

# File handler specifically for exclusion reasons (separate file for easier auditing)
exclusion_handler = RotatingFileHandler(
    EXCLUSION_LOG_FILE_PATH, maxBytes=10*1024*1024, backupCount=5
)
exclusion_handler.setLevel(logging.WARNING) # Log warnings and above as exclusions
exclusion_format = PipelineFormatter('%(asctime)s - %(levelname)s - %(message)s')
exclusion_handler.setFormatter(exclusion_format)

# Console handler for immediate feedback during execution
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_format = PipelineFormatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_format)

logger.addHandler(file_handler)
logger.addHandler(exclusion_handler)
logger.addHandler(console_handler)

def get_logger(name: str) -> logging.Logger:
    """
    Returns a named logger that inherits the configured handlers.
    """
    return logging.getLogger(name)

def log_pipeline_event(message: str, level: int = logging.INFO):
    """
    Logs a general pipeline event to the main log file and console.
    """
    logger.log(level, message)

def log_exclusion_reason(reason: str, details: Optional[str] = None):
    """
    Logs a specific exclusion reason to the exclusions.log file and the main log.
    This is used when data points are filtered out.
    """
    log_message = reason
    if details:
        log_message = f"{reason} (Details: {details})"
    
    # Log to the specific exclusion handler
    logger.warning(log_message, extra={'exclusion_reason': reason})
    
    # Also log to main info log for visibility
    logger.info(f"Exclusion logged: {reason}")