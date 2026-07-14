import os
import hashlib
import logging
import random
import numpy as np
from typing import Optional, Any, Callable, Union, List, Dict

logger = logging.getLogger(__name__)

def setup_logging(log_level: Union[str, int, None] = None, name: Optional[str] = None) -> logging.Logger:
    """
    Setup logging configuration.
    Tolerant to various call signatures:
    - setup_logging()
    - setup_logging("INFO")
    - setup_logging(log_level="INFO")
    - setup_logging(logging.INFO)
    - setup_logging(name="my_logger")
    - setup_logging(log_level="INFO", name="my_logger")
    """
    # Normalize log_level
    if log_level is None:
        level = logging.INFO
    elif isinstance(log_level, str):
        level = getattr(logging, log_level.upper(), logging.INFO)
    elif isinstance(log_level, int):
        level = log_level
    else:
        level = logging.INFO

    # Determine logger name
    logger_name = name if name else "llmXive"

    # Get or create logger
    log = logging.getLogger(logger_name)
    log.setLevel(level)

    # Avoid adding handlers multiple times
    if not log.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        log.addHandler(handler)

    return log

def pin_random_seed(seed: int) -> None:
    """Pin random seed for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def compute_file_checksum(filepath: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    # Test setup_logging
    log1 = setup_logging()
    log1.info("Default logging setup")
    
    log2 = setup_logging("DEBUG")
    log2.debug("Debug logging setup")
    
    log3 = setup_logging(log_level="WARNING", name="test_logger")
    log3.warning("Custom logger setup")

if __name__ == "__main__":
    main()
