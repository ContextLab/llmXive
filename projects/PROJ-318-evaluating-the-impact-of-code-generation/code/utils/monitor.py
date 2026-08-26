"""
Memory monitoring utility and logging infrastructure for llmXive.

Reads memory usage from /proc/self/status (Linux) to enforce RAM limits.
Configures project-wide logging to files and console.
"""
import logging
import os
import re
import sys
from pathlib import Path
from typing import Optional

# Ensure logging directory exists
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

# Configure project logger
def setup_logger(name: str, log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Sets up a logger that writes to both console and a specific log file.

    Args:
        name: Logger name (usually __name__)
        log_file: Relative path to log file (e.g., 'logs/monitor.log')
        level: Logging level

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers if logger already configured
    if logger.handlers:
        return logger

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        file_path = Path(log_file)
        file_path.parent.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(file_path)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

# Initialize the main project logger
logger = setup_logger('llmXive', 'logs/monitor.log')

class MemoryLimitException(Exception):
    """Raised when memory usage exceeds the configured limit."""
    pass

def get_memory_usage_mb() -> float:
    """
    Reads the current memory usage (VmRSS) from /proc/self/status.

    Returns:
        Current memory usage in Megabytes (float).

    Raises:
        OSError: If running on a non-Linux system or file not found.
        RuntimeError: If the memory value cannot be parsed.
    """
    if os.name != 'posix' or sys.platform == 'darwin' or sys.platform == 'win32':
        # Fallback for non-Linux systems: try /proc if available, else raise
        if not os.path.exists('/proc/self/status'):
            raise OSError("Memory monitoring via /proc/self/status is only supported on Linux.")

    try:
        with open('/proc/self/status', 'r') as f:
            for line in f:
                if line.startswith('VmRSS:'):
                    # Format: VmRSS:     1234 kB
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            kb_value = int(parts[1])
                            return kb_value / 1024.0
                        except ValueError:
                            raise RuntimeError(f"Could not parse VmRSS value: {line}")
            raise RuntimeError("VmRSS line not found in /proc/self/status")
    except FileNotFoundError:
        raise OSError("/proc/self/status not found. Memory monitoring requires Linux.")

def check_memory_limit(limit_mb: float = 7000.0, log_entry: str = "RAM_LIMIT_EXCEEDED") -> float:
    """
    Checks if current memory usage exceeds the specified limit.

    Args:
        limit_mb: Maximum allowed memory in MB (default 7000.0 MB / ~7 GB)
        log_entry: Specific log message to raise if limit exceeded

    Returns:
        Current memory usage in MB.

    Raises:
        MemoryLimitException: If memory usage exceeds limit_mb.
    """
    current_mb = get_memory_usage_mb()
    if current_mb > limit_mb:
        logger.error(f"{log_entry}: Current memory {current_mb:.2f} MB exceeds limit {limit_mb:.2f} MB")
        raise MemoryLimitException(
            f"Memory limit exceeded: {current_mb:.2f} MB > {limit_mb:.2f} MB"
        )
    logger.debug(f"Memory check passed: {current_mb:.2f} MB <= {limit_mb:.2f} MB")
    return current_mb

def log_memory_snapshot(message: str = "Memory Snapshot") -> float:
    """
    Logs the current memory usage with a custom message.

    Args:
        message: Contextual message for the log entry

    Returns:
        Current memory usage in MB.
    """
    current_mb = get_memory_usage_mb()
    logger.info(f"{message}: {current_mb:.2f} MB")
    return current_mb