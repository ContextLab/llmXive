import logging
import os
import sys
from pathlib import Path
from typing import Optional, Union

def get_project_root() -> Path:
    return Path(__file__).parent.parent.parent

def setup_logger(name: str, log_file: Optional[str] = None, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger

def get_logger(name: str) -> logging.Logger:
    return setup_logger(name)

def log_exception(e: Exception):
    logger = get_logger("exception")
    logger.error(str(e), exc_info=True)

def validate_log_directory():
    root = get_project_root()
    log_dir = root / "logs"
    log_dir.mkdir(exist_ok=True)

def main():
    print("Logger module loaded.")
