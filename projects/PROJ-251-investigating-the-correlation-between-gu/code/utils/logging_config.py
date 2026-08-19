"""
Logging configuration.
"""
import logging
import os
from pathlib import Path
from typing import Optional
import json
from datetime import datetime

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def log_exclusion_count(count: int, reason: str):
    pass

def log_sample_size(count: int):
    pass

def log_error_context(error: Exception):
    pass
