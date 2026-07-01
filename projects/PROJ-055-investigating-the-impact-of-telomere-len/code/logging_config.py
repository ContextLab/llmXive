"""
Logging configuration and memory monitoring utilities.
"""
import logging
import os
import sys
from pathlib import Path
from typing import Optional
import psutil

LOG_DIR = Path("logs")

def ensure_log_directory() -> Path:
    """Ensure the log directory exists."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    return LOG_DIR

def get_memory_usage_bytes() -> int:
    """Get current memory usage in bytes."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss

def check_memory_pressure(threshold_gb: float = 6.0) -> bool:
    """Check if memory usage exceeds threshold."""
    threshold_bytes = threshold_gb * (1024 ** 3)
    current = get_memory_usage_bytes()
    return current > threshold_bytes

def get_memory_status() -> Dict[str, Any]:
    """Get detailed memory status."""
    process = psutil.Process(os.getpid())
    return {
        "rss_bytes": process.memory_info().rss,
        "vms_bytes": process.memory_info().vms,
        "percent": process.memory_percent()
    }

def setup_logging(name: str, level: int = logging.INFO) -> logging.Logger:
    """Setup logging to file and console."""
    ensure_log_directory()
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if logger.handlers:
        return logger
    
    # File handler
    log_file = LOG_DIR / f"{name}.log"
    fh = logging.FileHandler(log_file)
    fh.setLevel(level)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)
    
    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger

def log_memory_status(logger: Optional[logging.Logger] = None) -> None:
    """Log current memory status."""
    if logger is None:
        logger = setup_logging("memory")
    status = get_memory_status()
    logger.info(f"Memory Status: RSS={status['rss_bytes']/1e6:.1f}MB, Percent={status['percent']:.1f}%")

def handle_memory_pressure(threshold_gb: float = 6.0) -> bool:
    """Handle memory pressure by logging and returning status."""
    if check_memory_pressure(threshold_gb):
        logger = setup_logging("memory")
        log_memory_status(logger)
        logger.warning(f"Memory pressure detected (> {threshold_gb}GB). Consider chunking or subsampling.")
        return True
    return False

def init_project_logging() -> None:
    """Initialize logging for the entire project."""
    ensure_log_directory()
    setup_logging("pipeline")
