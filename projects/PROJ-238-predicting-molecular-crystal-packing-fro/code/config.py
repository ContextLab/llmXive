import os
import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional

class Config:
    """Configuration manager for the project."""
    
    def __init__(self):
        self._config = {
            'COD_URL': os.getenv('COD_URL', 'http://www.crystallography.net/cod/'),
            'RANDOM_SEED': int(os.getenv('RANDOM_SEED', '42')),
            'DATA_PATH': os.getenv('DATA_PATH', 'data'),
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

_config_instance = None

def get_config() -> Config:
    """Get or create the global config instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance

class JsonFormatter(logging.Formatter):
    """Custom JSON formatter for logging."""
    
    def format(self, record):
        log_record = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)
        return json.dumps(log_record)

def setup_logging(log_level: str = 'INFO') -> None:
    """Setup logging configuration."""
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    logger.handlers = []
    
    # Add console handler with JSON formatting
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)

def get_env_var(name: str, default: str = '') -> str:
    """Get an environment variable with a default value."""
    return os.getenv(name, default)

def log_event(event_type: str, data: Dict[str, Any]) -> None:
    """Log an event as a structured JSON message."""
    logger = logging.getLogger()
    extra_data = {
        'event_type': event_type,
        **data
    }
    logger.info(json.dumps(extra_data))
