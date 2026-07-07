import logging
import os
import sys
import psutil
from pathlib import Path
from typing import Optional

# Constants
LOG_DIR = Path("logs")
MEMORY_THRESHOLD_BYTES = 6 * 1024**3  # 6 GB
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def ensure_log_directory() -> Path:
    """Ensure the log directory exists, creating it if necessary."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    return LOG_DIR

def get_memory_usage_bytes() -> int:
    """Get current process memory usage in bytes."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss

def check_memory_pressure() -> bool:
    """Check if current memory usage exceeds the 6GB threshold."""
    return get_memory_usage_bytes() > MEMORY_THRESHOLD_BYTES

def get_memory_status() -> dict:
    """Get detailed memory status information."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return {
        "rss_bytes": mem_info.rss,
        "vms_bytes": mem_info.vms,
        "percent": process.memory_percent(),
        "threshold_bytes": MEMORY_THRESHOLD_BYTES,
        "exceeds_threshold": check_memory_pressure()
    }

def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """
    Configure logging infrastructure.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional filename for file logging. If None, only logs to console.
        
    Returns:
        Configured logger instance.
    """
    ensure_log_directory()
    
    # Create logger
    logger = logging.getLogger("telomere_pipeline")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Clear existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        log_path = LOG_DIR / log_file
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger

def log_memory_status(logger: logging.Logger) -> None:
    """Log current memory status to the provided logger."""
    status = get_memory_status()
    logger.info(f"Memory Status: RSS={status['rss_bytes']:,}B, "
               f"Threshold={status['threshold_bytes']:,}B, "
               f"Exceeds: {status['exceeds_threshold']}")

def handle_memory_pressure(logger: logging.Logger) -> bool:
    """
    Check for memory pressure and log a warning if exceeded.
    
    Returns:
        True if memory pressure is detected, False otherwise.
    """
    if check_memory_pressure():
        status = get_memory_status()
        logger.warning(f"MEMORY PRESSURE DETECTED: Current usage ({status['rss_bytes']:,}B) "
                     f"exceeds threshold ({status['threshold_bytes']:,}B). "
                     f"Consider chunked processing or subsampling.")
        return True
    return False

def init_project_logging(log_file: str = "pipeline.log", log_level: str = "INFO") -> logging.Logger:
    """
    Initialize project-wide logging with memory pressure monitoring.
    
    Args:
        log_file: Name of the log file in the logs directory.
        log_level: Logging level.
        
    Returns:
        Configured logger instance.
    """
    logger = setup_logging(log_level=log_level, log_file=log_file)
    logger.info("Logging infrastructure initialized")
    log_memory_status(logger)
    
    # Initial memory pressure check
    if handle_memory_pressure(logger):
        logger.warning("Starting pipeline under memory pressure conditions.")
        
    return logger
