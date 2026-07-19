"""
Logging infrastructure and memory usage monitoring for the Gut Microbiome project.

This module provides:
- A centralized logging configuration (file + console).
- A memory usage monitor that logs current RAM consumption.
- Context managers and decorators to track memory usage of code blocks.
"""

import logging
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, Any, Generator

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    logging.warning("psutil not installed. Memory monitoring features will be disabled.")


# Constants
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_FILE_NAME = "pipeline.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Global logger instance
_logger: Optional[logging.Logger] = None


def get_logger(name: str = "gut_microbiome") -> logging.Logger:
    """
    Returns a configured logger instance.
    If not yet configured, it sets up file and console handlers.
    """
    global _logger
    if _logger is None:
        _logger = setup_logging(name)
    else:
        _logger = logging.getLogger(name)
    return _logger


def setup_logging(name: str = "gut_microbiome", log_level: int = logging.INFO) -> logging.Logger:
    """
    Configures the root logger for the project with file and console handlers.

    Args:
        name: The name for the logger.
        log_level: The logging level (e.g., logging.DEBUG, logging.INFO).

    Returns:
        A configured logger instance.
    """
    global _logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Prevent adding handlers multiple times if called repeatedly
    if logger.handlers:
        _logger = logger
        return logger

    # Ensure log directory exists
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file_path = LOG_DIR / LOG_FILE_NAME

    # File handler
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(log_level)
    file_formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    file_handler.setFormatter(file_formatter)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    _logger = logger
    logger.info(f"Logging initialized. Log file: {log_file_path}")
    return logger


def get_memory_usage_mb() -> Optional[float]:
    """
    Returns the current memory usage of the Python process in MB.

    Returns:
        Memory usage in MB, or None if psutil is not available.
    """
    if not HAS_PSUTIL:
        return None

    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 * 1024)  # Convert bytes to MB


def log_memory_usage(logger: Optional[logging.Logger] = None, message: str = "Current memory usage") -> float:
    """
    Logs the current memory usage and returns it.

    Args:
        logger: Logger instance to use. If None, uses the default 'gut_microbiome' logger.
        message: A message to include in the log.

    Returns:
        Current memory usage in MB, or -1.0 if unavailable.
    """
    if logger is None:
        logger = get_logger()

    mem_mb = get_memory_usage_mb()
    if mem_mb is not None:
        logger.info(f"{message}: {mem_mb:.2f} MB")
        return mem_mb
    else:
        logger.warning(f"{message}: psutil not available.")
        return -1.0


class MemoryMonitor:
    """
    A context manager to monitor memory usage within a code block.
    Logs the start, peak, and end memory usage.
    """

    def __init__(self, logger: Optional[logging.Logger] = None, tag: str = "MemoryMonitor"):
        self.logger = logger or get_logger()
        self.tag = tag
        self.start_mem: Optional[float] = None
        self.peak_mem: Optional[float] = None
        self.end_mem: Optional[float] = None

    def __enter__(self) -> "MemoryMonitor":
        if not HAS_PSUTIL:
            self.logger.warning(f"[{self.tag}] Memory monitoring disabled (psutil not installed).")
            return self

        self.start_mem = get_memory_usage_mb()
        self.peak_mem = self.start_mem
        self.logger.info(f"[{self.tag}] Start memory: {self.start_mem:.2f} MB")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not HAS_PSUTIL:
            return False

        self.end_mem = get_memory_usage_mb()
        if self.end_mem > self.peak_mem:
            self.peak_mem = self.end_mem

        self.logger.info(f"[{self.tag}] End memory: {self.end_mem:.2f} MB")
        self.logger.info(f"[{self.tag}] Peak memory: {self.peak_mem:.2f} MB")
        if self.start_mem:
            self.logger.info(f"[{self.tag}] Delta: {self.end_mem - self.start_mem:.2f} MB")

        return False


def monitor_memory(func: Callable) -> Callable:
    """
    A decorator to log memory usage before and after a function execution.

    Args:
        func: The function to wrap.

    Returns:
        The wrapped function.
    """
    def wrapper(*args, **kwargs) -> Any:
        logger = get_logger()
        logger.info(f"Starting function: {func.__name__}")

        if not HAS_PSUTIL:
            logger.warning("Memory monitoring disabled (psutil not installed).")
            return func(*args, **kwargs)

        start_mem = get_memory_usage_mb()
        logger.info(f"Function {func.__name__} start memory: {start_mem:.2f} MB")

        try:
            result = func(*args, **kwargs)
        except Exception as e:
            end_mem = get_memory_usage_mb()
            logger.error(f"Function {func.__name__} failed with exception: {e}")
            logger.error(f"Memory at failure: {end_mem:.2f} MB")
            raise

        end_mem = get_memory_usage_mb()
        logger.info(f"Function {func.__name__} end memory: {end_mem:.2f} MB")
        logger.info(f"Function {func.__name__} memory delta: {end_mem - start_mem:.2f} MB")

        return result
    return wrapper


def check_memory_limit(limit_mb: float = 7000.0, logger: Optional[logging.Logger] = None) -> bool:
    """
    Checks if current memory usage is within a specified limit.

    Args:
        limit_mb: The memory limit in MB (default 7000 MB ~ 7GB).
        logger: Logger instance to use.

    Returns:
        True if within limit, False otherwise.
    """
    if not HAS_PSUTIL:
        logger = logger or get_logger()
        logger.warning("Cannot check memory limit: psutil not installed.")
        return True  # Assume safe if we can't measure

    current_mem = get_memory_usage_mb()
    if logger:
        logger.info(f"Current memory: {current_mem:.2f} MB / Limit: {limit_mb:.2f} MB")

    if current_mem > limit_mb:
        if logger:
            logger.error(f"Memory limit exceeded! Current: {current_mem:.2f} MB, Limit: {limit_mb:.2f} MB")
        return False
    return True