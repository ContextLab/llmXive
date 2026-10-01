import logging
import sys
from pathlib import Path
from typing import Optional
from .config import get_config

def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(level)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    return logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    if name is None:
        name = __name__
    return setup_logger(name)

def main():
    logger = get_logger("test")
    logger.info("Logger test")

if __name__ == "__main__":
    main()