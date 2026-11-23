import os
import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path

class Config:
    """Configuration class for the project."""
    def __init__(self):
        self.COD_URL = os.getenv('COD_URL', 'https://www.crystallography.net/cod/')
        self.RANDOM_SEED = int(os.getenv('RANDOM_SEED', '42'))
        self.DATA_PATH = Path(os.getenv('DATA_PATH', 'data'))
        self.STATE_PATH = Path(os.getenv('STATE_PATH', 'state'))
        self.RESULTS_PATH = Path(os.getenv('RESULTS_PATH', 'results'))
    
    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

_config = None

def get_config() -> Config:
    """Get the singleton configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config

class JsonFormatter(logging.Formatter):
    """Custom JSON formatter for logging."""
    def format(self, record):
        log_record = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
        }
        return json.dumps(log_record)

def setup_logging(name: str, level: int = logging.INFO) -> logging.Logger:
    """Setup logging with JSON format."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
    
    return logger

def get_env_var(key: str, default: str = '') -> str:
    """Get an environment variable with a default value."""
    return os.getenv(key, default)

def log_event(event: str, data: Dict[str, Any] = None):
    """Log an event with optional data."""
    logger = logging.getLogger('event')
    log_data = {
        'event': event,
        'timestamp': datetime.utcnow().isoformat(),
    }
    if data:
        log_data.update(data)
    logger.info(json.dumps(log_data))