import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from config import get_path_env_override

# Define log file paths relative to project root
# The project root is assumed to be the parent of 'code/'
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGS_DIR = PROJECT_ROOT / "results" / "logs"

# Log formats
DATA_QUALITY_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
MODEL_DIAGNOSTICS_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

def ensure_directories():
    """Ensure the logs directory exists."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

def setup_logging():
    """
    Configure root logging and return handlers for specific loggers.
    This function sets up the logging infrastructure to write to files
    in results/logs/ as required by the project.
    """
    ensure_directories()
    
    # Prevent adding handlers multiple times if called repeatedly
    root_logger = logging.getLogger()
    if root_logger.handlers:
        # If handlers already exist, we assume logging is already configured
        # But we ensure the file paths are valid for new loggers if needed
        pass

    # Create file handlers
    data_quality_log_path = LOGS_DIR / "data_quality.log"
    model_diagnostics_log_path = LOGS_DIR / "model_diagnostics.log"
    
    # Data Quality Handler
    fh_dq = logging.FileHandler(data_quality_log_path)
    fh_dq.setLevel(logging.INFO)
    fh_dq.setFormatter(logging.Formatter(DATA_QUALITY_FORMAT))
    
    # Model Diagnostics Handler
    fh_md = logging.FileHandler(model_diagnostics_log_path)
    fh_md.setLevel(logging.INFO)
    fh_md.setFormatter(logging.Formatter(MODEL_DIAGNOSTICS_FORMAT))

    # Create specific loggers
    data_quality_logger = logging.getLogger("data_quality")
    data_quality_logger.setLevel(logging.INFO)
    # Remove existing handlers to avoid duplicates if called again
    data_quality_logger.handlers.clear()
    data_quality_logger.addHandler(fh_dq)
    
    model_diagnostics_logger = logging.getLogger("model_diagnostics")
    model_diagnostics_logger.setLevel(logging.INFO)
    model_diagnostics_logger.handlers.clear()
    model_diagnostics_logger.addHandler(fh_md)

    # Also configure a general project logger for mixed logs if needed
    general_logger = logging.getLogger("project")
    general_logger.setLevel(logging.INFO)
    general_logger.handlers.clear()
    # Add both handlers to general logger for broad capture
    general_logger.addHandler(fh_dq)
    general_logger.addHandler(fh_md)

    return data_quality_logger, model_diagnostics_logger

def get_data_quality_logger():
    """
    Get the configured data quality logger.
    Initializes logging if not already done.
    """
    setup_logging()
    return logging.getLogger("data_quality")

def get_model_diagnostics_logger():
    """
    Get the configured model diagnostics logger.
    Initializes logging if not already done.
    """
    setup_logging()
    return logging.getLogger("model_diagnostics")

def main():
    """
    Main entry point for testing the logging setup.
    Writes a test entry to both log files to verify functionality.
    """
    dq_logger, md_logger = setup_logging()
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    dq_logger.info(f"[T011] Logging infrastructure initialized. Test log written at {timestamp}.")
    dq_logger.info(f"[T011] Data quality logs will be written to: {LOGS_DIR / 'data_quality.log'}")
    
    md_logger.info(f"[T011] Model diagnostics logger initialized. Test log written at {timestamp}.")
    md_logger.info(f"[T011] Model diagnostics logs will be written to: {LOGS_DIR / 'model_diagnostics.log'}")
    
    print(f"Logging setup complete. Check {LOGS_DIR} for log files.")

if __name__ == "__main__":
    main()