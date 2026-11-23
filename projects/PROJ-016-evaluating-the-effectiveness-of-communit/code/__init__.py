"""
llmXive Project Initialization.
Configures logging infrastructure as per T005.
"""
import logging
import logging.config
import os
import sys
from pathlib import Path

# Ensure logs directory exists
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
logs_dir = project_root / "logs"
logs_dir.mkdir(parents=True, exist_ok=True)
log_file_path = logs_dir / "run.log"

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json_formatter': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
        },
        'simple': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'simple',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'INFO',
            'formatter': 'json_formatter',
            'filename': str(log_file_path),
            'maxBytes': 10485760,  # 10 MB
            'backupCount': 5
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console', 'file']
    }
}

# Apply the configuration
logging.config.dictConfig(LOGGING_CONFIG)

def get_logger(name=None):
    """
    Get a logger instance.
    
    Args:
        name: Logger name. If None, returns the root logger.
    
    Returns:
        logging.Logger: Configured logger instance.
    """
    return logging.getLogger(name)
