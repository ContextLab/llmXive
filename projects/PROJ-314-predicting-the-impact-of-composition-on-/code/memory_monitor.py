"""
Memory monitoring utilities for the llmXive pipeline.
Implements strict memory usage checks to prevent exceeding system limits.
"""
import os
import sys
import logging
import gc
from pathlib import Path
from typing import Optional, Dict, Any

# Try to import psutil; if missing, we fail loudly as per project constraints
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    logging.warning("psutil not installed. Memory monitoring disabled. Install with: pip install psutil")

from .config import get_int_config
from . import logger

# Ensure logs directory exists
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)
MEMORY_LOG_PATH = LOGS_DIR / "memory_monitor.log"

def _get_logger() -> logging.Logger:
    """Get the logger configured for memory monitoring."""
    return logger

def get_memory_usage_gb(process: Optional[Any] = None) -> float:
    """
    Get the current memory usage of the process in GB.
    
    Args:
        process: Optional psutil Process object. If None, uses current process.
    
    Returns:
        Memory usage in GB.
    
    Raises:
        RuntimeError: If psutil is not available.
    """
    if not HAS_PSUTIL:
        raise RuntimeError("psutil is required for memory monitoring but is not installed.")
    
    if process is None:
        process = psutil.Process(os.getpid())
    
    # Get memory info (RSS - Resident Set Size)
    mem_info = process.memory_info()
    return mem_info.rss / (1024 ** 3)  # Convert bytes to GB

def check_memory_limit(limit_gb: Optional[int] = None) -> bool:
    """
    Check if current memory usage is within the specified limit.
    
    Args:
        limit_gb: Memory limit in GB. Defaults to config value (default 6GB).
    
    Returns:
        True if within limit, False otherwise.
    
    Raises:
        RuntimeError: If psutil is not available.
        MemoryError: If memory usage exceeds the limit.
    """
    if not HAS_PSUTIL:
        # If psutil is not available, we cannot check memory. 
        # Per task requirements, we should fail loudly if we can't monitor.
        # However, for robustness, we might allow execution if the user explicitly
        # disables monitoring, but the task spec says "raise MemoryError if > 6GB".
        # Since we can't check, we raise an error to force installation.
        raise RuntimeError("psutil is required for memory monitoring. Please install it.")
    
    if limit_gb is None:
        limit_gb = get_int_config("MEMORY_LIMIT_GB", default=6)
    
    current_usage = get_memory_usage_gb()
    
    if current_usage > limit_gb:
        msg = f"Memory limit exceeded: {current_usage:.2f}GB > {limit_gb}GB"
        _log_memory_event("ERROR", msg)
        raise MemoryError(msg)
    
    _log_memory_event("INFO", f"Memory usage OK: {current_usage:.2f}GB <= {limit_gb}GB")
    return True

def force_garbage_collection() -> None:
    """Force garbage collection to free up memory."""
    gc.collect()
    if HAS_PSUTIL:
        current = get_memory_usage_gb()
        _log_memory_event("INFO", f"Garbage collection triggered. Current usage: {current:.2f}GB")
    else:
        _log_memory_event("INFO", "Garbage collection triggered.")

def validate_dataset_size(file_path: str, limit_gb: Optional[int] = None) -> bool:
    """
    Validate that a dataset file size is within the memory limit.
    
    Args:
        file_path: Path to the dataset file.
        limit_gb: Memory limit in GB.
    
    Returns:
        True if file size is within limit, False otherwise.
    
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Dataset file not found: {file_path}")
    
    file_size_bytes = os.path.getsize(file_path)
    file_size_gb = file_size_bytes / (1024 ** 3)
    
    if limit_gb is None:
        limit_gb = get_int_config("MEMORY_LIMIT_GB", default=6)
    
    if file_size_gb > limit_gb:
        msg = f"Dataset file too large: {file_size_gb:.2f}GB > {limit_gb}GB limit"
        _log_memory_event("WARNING", msg)
        return False
    
    _log_memory_event("INFO", f"Dataset size OK: {file_size_gb:.2f}GB <= {limit_gb}GB")
    return True

def _log_memory_event(level: str, message: str) -> None:
    """Log a memory event to both the logger and the memory_monitor.log file."""
    timestamp = __import__('time').strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {level}: {message}"
    
    # Log to the main logger
    if level == "ERROR":
        logger.error(message)
    elif level == "WARNING":
        logger.warning(message)
    else:
        logger.info(message)
    
    # Log to the specific memory monitor log file
    try:
        with open(MEMORY_LOG_PATH, "a") as f:
            f.write(log_entry + "\n")
    except IOError as e:
        logger.error(f"Failed to write to memory monitor log: {e}")

def log_memory_usage(label: str = "Current") -> None:
    """
    Log the current memory usage with a label.
    
    Args:
        label: Label for the memory usage log entry.
    """
    if HAS_PSUTIL:
        usage = get_memory_usage_gb()
        _log_memory_event("INFO", f"{label} memory usage: {usage:.2f}GB")
    else:
        _log_memory_event("WARNING", f"{label} memory usage: Unable to measure (psutil not installed)")

def main() -> None:
    """
    Main entry point for memory monitoring.
    This function can be called to perform a self-check of memory usage.
    """
    _log_memory_event("INFO", "Memory monitor started.")
    log_memory_usage("Initial")
    
    try:
        check_memory_limit()
        _log_memory_event("INFO", "Memory check passed.")
    except MemoryError as e:
        _log_memory_event("ERROR", str(e))
        sys.exit(1)
    except RuntimeError as e:
        _log_memory_event("ERROR", str(e))
        sys.exit(1)
    
    _log_memory_event("INFO", "Memory monitor finished.")

if __name__ == "__main__":
    main()
