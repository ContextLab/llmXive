import logging
import os
import sys
import time
from typing import Optional, Dict, Any
import psutil

def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Sets up a logger that writes to both console and a file.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler (optional, depending on project structure)
    # We assume logs are written to a specific directory if needed, 
    # but for this utility, console is primary.
    
    return logger

def get_resource_usage() -> Dict[str, Any]:
    """
    Get current memory and CPU usage.
    """
    process = psutil.Process(os.getpid())
    return {
        "memory_mb": process.memory_info().rss / 1024 / 1024,
        "cpu_percent": process.cpu_percent(interval=0.1)
    }

def log_memory_usage(logger: Optional[logging.Logger] = None, message: str = ""):
    """
    Logs the current memory usage.
    """
    usage = get_resource_usage()
    log_msg = f"{message} Memory Usage: {usage['memory_mb']:.2f} MB"
    if logger:
        logger.info(log_msg)
    else:
        print(log_msg)

class Timer:
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger
        self.start_time = None
        self.elapsed = 0.0

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed = time.time() - self.start_time
        msg = f"Elapsed time: {self.elapsed:.2f} seconds"
        if self.logger:
            self.logger.info(msg)
        else:
            print(msg)
