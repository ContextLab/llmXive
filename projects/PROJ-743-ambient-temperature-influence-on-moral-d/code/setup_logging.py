"""
Logging infrastructure setup for the project.
Configures loggers to write to results/logs/
"""
import os
import sys
import logging
from datetime import datetime
from pathlib import Path

from config import get_path_env_override

def ensure_directories():
    """Ensure the results/logs directory exists."""
    log_dir = Path("results/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir

def setup_logging():
    """
    Configure the root logger and specific loggers for the project.
    Writes data quality logs and model diagnostics to results/logs/.
    """
    ensure_directories()
    
    log_file_path = ensure_directories() / "pipeline.log"
    
    # Create a custom formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # File handler
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Avoid adding handlers multiple times if this is called repeatedly
    if not root_logger.handlers:
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

    return root_logger

def get_data_quality_logger():
    """
    Get a specific logger for data quality tasks.
    """
    logger = logging.getLogger('data_quality')
    logger.setLevel(logging.DEBUG)
    if not logger.handlers:
        # Reuse handlers from root or create specific ones
        # For simplicity, we let the root handler configuration propagate
        # but we ensure the file path is correct for this specific logger if needed.
        # In this setup, we rely on the root logger's file handler.
        pass
    return logger

def get_model_diagnostics_logger():
    """
    Get a specific logger for model diagnostics.
    """
    logger = logging.getLogger('model_diagnostics')
    logger.setLevel(logging.DEBUG)
    return logger

def main():
    """Entry point to initialize logging."""
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Logging infrastructure initialized.")
    logger.info(f"Log file location: results/logs/pipeline.log")

if __name__ == "__main__":
    main()