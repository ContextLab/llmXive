import logging
import sys
from typing import Optional

def get_process_memory_mb() -> float:
    """Get current process memory usage in MB."""
    try:
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)
    except ImportError:
        logging.warning("psutil not installed, memory tracking disabled")
        return 0.0

def setup_memory_logger(name: str = "memory_monitor", level: int = logging.INFO):
    """Set up a logger for memory monitoring."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

def log_memory_snapshot(logger: logging.Logger, stage: str):
    """Log a memory snapshot for the current stage."""
    memory_mb = get_process_memory_mb()
    logger.info(f"Memory snapshot at {stage}: {memory_mb:.2f} MB")
