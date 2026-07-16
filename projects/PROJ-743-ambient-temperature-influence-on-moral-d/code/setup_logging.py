import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from config import get_path_env_override

# Define log directory based on project structure
LOG_DIR = Path("results/logs")

# Ensure the log directory exists
def _ensure_log_dir():
    LOG_DIR.mkdir(parents=True, exist_ok=True)

# Configure the root logger for the project
def setup_logging():
    _ensure_log_dir()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Data Quality Log file
    data_quality_log_path = LOG_DIR / f"data_quality_{timestamp}.log"
    
    # Model Diagnostics Log file
    model_diagnostics_log_path = LOG_DIR / f"model_diagnostics_{timestamp}.log"
    
    # Configure root logger to avoid duplicate handlers if called multiple times
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        root_logger.setLevel(logging.INFO)
        # Optional: Console handler for immediate feedback
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        root_logger.addHandler(console_handler)

    return data_quality_log_path, model_diagnostics_log_path

def get_data_quality_logger(name: str = "data_quality"):
    """
    Returns a logger instance that writes data quality logs to results/logs/.
    This logger is intended for ingestion validation, filtering stats, and data integrity checks.
    """
    _ensure_log_dir()
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Avoid adding duplicate handlers if this is called multiple times
    if not logger.handlers:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = LOG_DIR / f"data_quality_{timestamp}.log"
        
        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    return logger

def get_model_diagnostics_logger(name: str = "model_diagnostics"):
    """
    Returns a logger instance that writes model diagnostics to results/logs/.
    This logger is intended for convergence checks, residual analysis, and coefficient logging.
    """
    _ensure_log_dir()
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = LOG_DIR / f"model_diagnostics_{timestamp}.log"
        
        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    return logger

def main():
    """
    Entry point to demonstrate logging infrastructure setup.
    Creates log files and writes initial startup entries.
    """
    print("Setting up logging infrastructure...")
    setup_logging()
    
    dq_logger = get_data_quality_logger()
    md_logger = get_model_diagnostics_logger()
    
    dq_logger.info("Data Quality Logger initialized successfully.")
    dq_logger.info("Ready to log ingestion validation results.")
    
    md_logger.info("Model Diagnostics Logger initialized successfully.")
    md_logger.info("Ready to log model convergence and parameter estimates.")
    
    print(f"Logs will be written to: {LOG_DIR}")
    print("Logging infrastructure setup complete.")

if __name__ == "__main__":
    main()
