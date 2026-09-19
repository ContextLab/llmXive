import logging
import logging.config
import os
import yaml
from pathlib import Path
from typing import Optional

def setup_logging():
    """Setup logging configuration."""
    config_path = Path("code/config/logging.yaml")
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            logging.config.dictConfig(config)
    else:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    return logging.getLogger(__name__)

def log_timeout(message: str):
    """Log a timeout message."""
    logger = setup_logging()
    logger.error(f"TIMEOUT: {message}")

def log_missing_data(message: str):
    """Log a missing data message."""
    logger = setup_logging()
    logger.warning(f"MISSING DATA: {message}")
