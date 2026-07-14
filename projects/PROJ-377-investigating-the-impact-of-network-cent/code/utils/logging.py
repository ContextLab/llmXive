"""
Logging Infrastructure Module.

Implements T005: Setup logging infrastructure to track wall_clock_time and RAM usage.
"""
import logging
import os
import sys
import time
from typing import Optional, Dict, Any
import psutil

def setup_logger(name: str, log_file: Optional[str] = None, level=logging.INFO) -> logging.Logger:
    """
    Sets up a logger with console and optional file handler.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # File handler (if log_file provided)
        if log_file:
            os.makedirs(os.path.dirname(log_file) if os.path.dirname(log_file) else ".", exist_ok=True)
            fh = logging.FileHandler(log_file)
            fh.setLevel(level)
            fh.setFormatter(formatter)
            logger.addHandler(fh)

    return logger

def get_resource_usage() -> Dict[str, Any]:
    """
    Returns current RAM usage and process info.
    """
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return {
        "rss_mb": mem_info.rss / (1024 * 1024),
        "vms_mb": mem_info.vms / (1024 * 1024),
        "cpu_percent": process.cpu_percent()
    }

def log_memory_usage(logger: logging.Logger, message: str):
    """
    Logs a message with current memory usage.
    """
    usage = get_resource_usage()
    logger.info(f"{message} - RAM: {usage['rss_mb']:.2f} MB")

class Timer:
    """
    Context manager for timing code blocks (wall_clock_time).
    """
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        elapsed = self.end_time - self.start_time
        if self.logger:
            self.logger.info(f"Elapsed time: {elapsed:.2f} seconds")
        return False