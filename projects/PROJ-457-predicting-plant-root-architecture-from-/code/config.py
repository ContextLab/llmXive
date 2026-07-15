import os
import sys
import logging
import yaml
from pathlib import Path
from typing import Any, Dict

CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"

def get_config() -> Dict[str, Any]:
    """
    Loads configuration from config.yaml.
    """
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Configuration file not found at {CONFIG_PATH}")
    
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Configures logging to file and console.
    """
    logger = logging.getLogger("llmXive")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Clear existing handlers
    logger.handlers = []
    
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    # File handler (optional, based on config)
    # log_file = Path(get_config().get("LOG_PATH", "logs/pipeline.log"))
    # if not log_file.parent.exists():
    #     log_file.parent.mkdir(parents=True, exist_ok=True)
    # fh = logging.FileHandler(log_file)
    # fh.setFormatter(formatter)
    # logger.addHandler(fh)
    
    return logger
