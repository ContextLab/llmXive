import logging
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

class LlmXiveFormatter(logging.Formatter):
    def format(self, record):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"[{timestamp}] {record.levelname:<8} - {record.message}"

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(LlmXiveFormatter())
    logger.addHandler(handler)
    
    return logger

def setup_project_logger(name: str, log_file: Optional[Path] = None) -> logging.Logger:
    logger = get_logger(name)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(LlmXiveFormatter())
        logger.addHandler(file_handler)
    return logger

def get_console_only_logger(name: str) -> logging.Logger:
    return get_logger(name)

def get_logger_config() -> Dict[str, Any]:
    return {"level": "INFO", "formatter": "LlmXiveFormatter"}

def log_error(logger: logging.Logger, msg: str) -> None:
    logger.error(msg)

def log_fatal(logger: logging.Logger, msg: str) -> None:
    logger.critical(msg)
    sys.exit(1)
