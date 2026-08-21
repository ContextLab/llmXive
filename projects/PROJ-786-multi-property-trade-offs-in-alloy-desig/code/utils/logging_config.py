import logging
import json
import sys
import uuid
import os
from datetime import datetime

def get_logger(name: str = __name__) -> logging.Logger:
    return logging.getLogger(name)

def configure_root_logger():
    """Configures the root logger with JSON formatting and file rotation."""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File Handler (with rotation)
    from logging.handlers import RotatingFileHandler
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    file_handler = RotatingFileHandler(f"{log_dir}/pipeline.log", maxBytes=10*1024*1024, backupCount=5)
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

class StructuredFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "context": getattr(record, 'context', None)
        }
        return json.dumps(log_data)

class ContextFilter(logging.Filter):
    def __init__(self, context: str = None):
        self.context = context

    def filter(self, record):
        if self.context:
            record.context = self.context
        return True

def log_info_with_context(message: str, context: str = None):
    logger = logging.getLogger()
    extra = {'context': context} if context else {}
    logger.info(message, extra=extra)

def log_warning_with_context(message: str, context: str = None):
    logger = logging.getLogger()
    extra = {'context': context} if context else {}
    logger.warning(message, extra=extra)

def log_error_with_context(message: str, context: str = None):
    logger = logging.getLogger()
    extra = {'context': context} if context else {}
    logger.error(message, extra=extra)
