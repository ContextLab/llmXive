"""
Logging infrastructure setup.
Ensures log files are written to results/logs/
"""
import os
import sys
import logging
from datetime import datetime
from pathlib import Path

from config import get_path_env_override

def ensure_directories():
    """Create necessary log directories if they don't exist."""
    log_dir = Path(get_path_env_override('LOG_DIR', 'results/logs'))
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir

def setup_logging():
    """Configure basic logging to console and file."""
    log_dir = ensure_directories()
    log_file = log_dir / f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def get_data_quality_logger():
    """Get a specific logger for data quality checks."""
    logger = logging.getLogger('data_quality')
    if not logger.handlers:
        handler = logging.FileHandler(ensure_directories() / 'data_quality.log')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def get_model_diagnostics_logger():
    """Get a specific logger for model diagnostics."""
    logger = logging.getLogger('model_diagnostics')
    if not logger.handlers:
        handler = logging.FileHandler(ensure_directories() / 'model_diagnostics.log')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def main():
    """Entry point for logging setup."""
    logger = setup_logging()
    logger.info("Logging infrastructure initialized.")

if __name__ == '__main__':
    main()
