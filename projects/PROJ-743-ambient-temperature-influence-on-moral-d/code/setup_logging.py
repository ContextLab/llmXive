import os
import sys
import logging
from datetime import datetime
from pathlib import Path

def ensure_directories():
    """Ensures required log directories exist."""
    Path("results/logs").mkdir(parents=True, exist_ok=True)

def setup_logging():
    """Configures the root logger."""
    ensure_directories()
    log_file = Path("results/logs/data_quality_log.txt")
    
    # Avoid adding duplicate handlers if called multiple times
    if not any(isinstance(h, logging.FileHandler) for h in logging.root.handlers):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )

def get_data_quality_logger():
    """Returns a logger instance for data quality tasks."""
    return logging.getLogger("data_quality")

def get_model_diagnostics_logger():
    """Returns a logger instance for model diagnostics."""
    return logging.getLogger("model_diagnostics")

def main():
    """Entry point for logging setup."""
    setup_logging()

if __name__ == "__main__":
    main()
