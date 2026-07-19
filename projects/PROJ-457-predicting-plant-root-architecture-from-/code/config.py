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
        # Fallback to defaults if config.yaml is missing during setup
        return {
            "LOG_LEVEL": "INFO",
            "LOG_PATH": "logs/pipeline.log",
            "SEED": 42,
            "DATA_PATH": "data"
        }
    
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Configures logging to file and console.
    
    Reads LOG_LEVEL and LOG_PATH from config.yaml if available.
    Creates the log directory if it does not exist.
    """
    # Get config to determine paths and levels
    try:
        config = get_config()
        cfg_level = config.get("LOG_LEVEL", log_level)
        cfg_log_path = config.get("LOG_PATH", "logs/pipeline.log")
    except Exception:
        # Fallback if config loading fails
        cfg_level = log_level
        cfg_log_path = "logs/pipeline.log"

    level = getattr(logging, cfg_level.upper(), logging.INFO)
    
    logger = logging.getLogger("llmXive")
    logger.setLevel(level)
    
    # Clear existing handlers to prevent duplicates on re-calls
    logger.handlers = []
    
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    # File handler
    log_file = Path(cfg_log_path)
    if not log_file.parent.exists():
        log_file.parent.mkdir(parents=True, exist_ok=True)
    
    fh = logging.FileHandler(log_file)
    fh.setLevel(level)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    return logger