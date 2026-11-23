import logging
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional

# Try to import psutil for memory monitoring, but make it optional if not installed
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    # Only warn once at module load if psutil is missing, not every time a function is called
    # logging.warning("psutil not installed. Memory monitoring will be limited.")

# Global logger instance
_logger: Optional[logging.Logger] = None
_log_file_path: Optional[Path] = None

def get_memory_usage_mb() -> float:
    """Returns current memory usage in MB."""
    if not HAS_PSUTIL:
        return 0.0
    try:
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return 0.0

def log_memory_usage(logger: logging.Logger, message: str = ""):
    """Logs current memory usage."""
    mem = get_memory_usage_mb()
    logger.info(f"Memory Usage: {mem:.2f} MB {message}")

class MemoryMonitor:
    """Context manager to monitor memory usage."""
    def __init__(self, logger: logging.Logger, threshold_mb: float = 7000.0):
        self.logger = logger
        self.threshold_mb = threshold_mb
        self.start_mem = 0.0
        self.end_mem = 0.0

    def __enter__(self):
        self.start_mem = get_memory_usage_mb()
        self.logger.info(f"Memory Monitor Started. Start: {self.start_mem:.2f} MB")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_mem = get_memory_usage_mb()
        diff = self.end_mem - self.start_mem
        self.logger.info(f"Memory Monitor Ended. End: {self.end_mem:.2f} MB. Delta: {diff:.2f} MB")
        if self.end_mem > self.threshold_mb:
            self.logger.warning(f"Memory usage {self.end_mem:.2f} MB exceeds threshold {self.threshold_mb:.2f} MB")
        return False

def monitor_memory(logger: logging.Logger, threshold_mb: float = 7000.0):
    """Decorator to monitor memory usage of a function."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            mem_start = get_memory_usage_mb()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                mem_end = get_memory_usage_mb()
                logger.info(f"Function {func.__name__} memory delta: {mem_end - mem_start:.2f} MB")
        return wrapper
    return decorator

def check_memory_limit(limit_mb: float = 7000.0):
    """Checks if current memory usage exceeds limit and raises an error if so."""
    current = get_memory_usage_mb()
    if current > limit_mb:
        raise MemoryError(f"Memory limit exceeded: {current:.2f} MB > {limit_mb:.2f} MB")

def setup_logging(log_file: str = "data/processed/run.log", level: int = logging.INFO) -> logging.Logger:
    """
    Configures the root logger to write to a file and console.
    Ensures the directory for the log file exists.
    """
    global _logger, _log_file_path

    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    _log_file_path = log_path

    if _logger is not None:
        # If logger already exists, ensure it's still pointing to the correct file
        # If the log file path has changed, we might need to reconfigure handlers
        # For simplicity, we just return the existing logger if it's already set up
        # In a more complex scenario, we might want to reconfigure handlers if the path changed
        return _logger

    _logger = logging.getLogger("llmXive_pipeline")
    _logger.setLevel(level)

    # Clear existing handlers to avoid duplicates on re-calls
    if _logger.handlers:
        _logger.handlers.clear()

    # File handler
    fh = logging.FileHandler(log_path)
    fh.setLevel(level)
    
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    _logger.addHandler(fh)
    _logger.addHandler(ch)

    _logger.info(f"Logging initialized to {log_path}")
    return _logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Returns a logger, creating one if not yet configured."""
    global _logger
    if _logger is None:
        setup_logging()
    if name:
        return _logger.getChild(name)
    return _logger

def log_exception(logger: logging.Logger, exc: Exception):
    """Logs the full traceback of an exception."""
    logger.error(f"Exception occurred: {str(exc)}")
    logger.error(traceback.format_exc())

# If this module is run directly, set up logging and demonstrate functionality
if __name__ == "__main__":
    logger = setup_logging()
    logger.info("Logging infrastructure test started.")
    
    with MemoryMonitor(logger, threshold_mb=7000.0):
        logger.info("Simulating some work...")
        time.sleep(1)
        logger.info("Work simulated.")
    
    log_memory_usage(logger, "Final check.")
    logger.info("Logging infrastructure test completed.")
    print(f"Log file created at: {_log_file_path}")