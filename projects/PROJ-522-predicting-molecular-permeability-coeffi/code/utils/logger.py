import logging
import logging.config
import os
import yaml
from pathlib import Path
from typing import Optional

def setup_logging(config_path: Optional[str] = None):
    """
    Setup logging configuration.
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config" / "logging.yaml"
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            logging.config.dictConfig(config)
    else:
        # Fallback to basic config
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

def log_timeout(operation: str, timeout_minutes: int):
    """
    Log a timeout event.
    """
    logger = logging.getLogger(__name__)
    logger.warning(f"TIMEOUT: {operation} exceeded {timeout_minutes} minutes")

def log_missing_data(reason: str):
    """
    Log missing data event.
    """
    logger = logging.getLogger(__name__)
    logger.warning(f"Missing data: {reason}")
