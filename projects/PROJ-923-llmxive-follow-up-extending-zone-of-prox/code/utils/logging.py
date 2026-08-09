import logging
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from config import get_config, Config

_logger_registry: Dict[str, logging.Logger] = {}

def get_logger(name: str) -> logging.Logger:
    if name not in _logger_registry:
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        _logger_registry[name] = logger
    return _logger_registry[name]

def initialize_logging(level: Optional[str] = None):
    config = get_config()
    log_level = level or config.logging.get("level", "INFO")
    set_log_level(log_level)

def set_log_level(level: str):
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    for logger in _logger_registry.values():
        logger.setLevel(numeric_level)

def configure_logger(name: str, level: str, file_path: Optional[str] = None):
    logger = get_logger(name)
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    if file_path:
        handler = logging.FileHandler(file_path)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

def debug(msg: str, logger_name: str = "root"):
    get_logger(logger_name).debug(msg)

def info(msg: str, logger_name: str = "root"):
    get_logger(logger_name).info(msg)

def warning(msg: str, logger_name: str = "root"):
    get_logger(logger_name).warning(msg)

def error(msg: str, logger_name: str = "root"):
    get_logger(logger_name).error(msg)

def critical(msg: str, logger_name: str = "root"):
    get_logger(logger_name).critical(msg)
