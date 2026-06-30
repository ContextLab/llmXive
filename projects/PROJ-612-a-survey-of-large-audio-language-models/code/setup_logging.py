import logging
import os
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Optional

# Ensure the data and logs directories exist relative to project root
# We assume the project root is the parent of 'code'
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
LOG_FILE_PATH = LOGS_DIR / "pipeline.log"

# Ensure logs directory exists
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Define a custom formatter to include timestamp, level, and message
# Format: YYYY-MM-DD HH:MM:SS,ms | LEVEL | MODULE | MESSAGE
class ReproducibleFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        # Use ISO format or a fixed standard format for reproducibility
        # Including milliseconds for precision
        ct = datetime.fromtimestamp(record.created)
        if datefmt:
            return ct.strftime(datefmt)
        else:
            return ct.strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]

    def format(self, record):
        # Add module name for traceability
        record.module_name = record.name
        return super().format(record)

def get_logger(name: str = "llmXive_pipeline") -> logging.Logger:
    """
    Configures and returns a logger that writes to pipeline.log.
    Ensures only one handler is added per logger name to prevent duplicates
    in long-running scripts or repeated imports.
    """
    logger = logging.getLogger(name)
    
    # If logger already has handlers, return it to avoid duplicate logs
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)

    # Create file handler
    file_handler = RotatingFileHandler(
        LOG_FILE_PATH,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)

    # Create console handler for immediate feedback during development
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    # Create formatter
    formatter = ReproducibleFormatter(
        fmt="%(asctime)s | %(levelname)-8s | %(module_name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S,%f"
    )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Prevent propagation to root logger to avoid double logging if root is configured
    logger.propagate = False

    return logger

def init_logging() -> logging.Logger:
    """
    Initializes the global logging infrastructure.
    Returns the configured logger instance.
    """
    logger = get_logger()
    logger.info("Logging infrastructure initialized.")
    logger.info(f"Log file path: {LOG_FILE_PATH}")
    return logger

# Initialize logger immediately upon module import for convenience
# This ensures that any script importing this module starts logging immediately
logger = init_logging()

def log_pipeline_start() -> None:
    """Logs the start of a pipeline run with a timestamp."""
    logger.info("Pipeline run started.")

def log_pipeline_end() -> None:
    """Logs the successful completion of a pipeline run."""
    logger.info("Pipeline run completed successfully.")

def log_error(error: Exception, context: str = "General Error") -> None:
    """Logs an exception with context."""
    logger.error(f"{context}: {str(error)}", exc_info=True)

if __name__ == "__main__":
    # Test the logging setup when run directly
    test_logger = get_logger("test_runner")
    test_logger.debug("This is a debug message.")
    test_logger.info("This is an info message.")
    test_logger.warning("This is a warning message.")
    test_logger.error("This is an error message.")
    test_logger.critical("This is a critical message.")
    print(f"Logs written to: {LOG_FILE_PATH}")
