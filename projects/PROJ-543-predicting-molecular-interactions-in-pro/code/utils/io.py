import os
import sys
import time
import logging
import traceback
from contextlib import contextmanager
from typing import Optional, Callable, Any, Generator

try:
    import resource
    import psutil
    HAS_RESOURCE = True
    HAS_PSUTIL = True
except ImportError:
    HAS_RESOURCE = False
    HAS_PSUTIL = False

# SC-005: Maximum allowed memory footprint in GB
MEMORY_LIMIT_GB = 7.0
MEMORY_LIMIT_MB = MEMORY_LIMIT_GB * 1024

logger = logging.getLogger(__name__)

def setup_logging(name: str = "project", log_level: int = logging.INFO) -> logging.Logger:
    """
    Configures a standard logger for the project.
    """
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    root_logger = logging.getLogger(name)
    root_logger.setLevel(log_level)
    root_logger.addHandler(handler)
    
    return root_logger

def get_memory_usage_mb() -> float:
    """
    Returns the current memory usage of the process in Megabytes.
    Uses psutil if available, otherwise falls back to resource (Unix only).
    Raises RuntimeError if neither method is available.
    """
    if HAS_PSUTIL:
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)
    
    if HAS_RESOURCE:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # ru_maxrss is in kilobytes on Linux/macOS
        return usage.ru_maxrss / 1024.0
    
    raise RuntimeError(
        "Memory monitoring requires 'psutil' or 'resource' (Unix). "
        "Install psutil: pip install psutil"
    )

def check_memory_limit(current_mb: Optional[float] = None) -> bool:
    """
    Checks if the current memory usage is within the SC-005 limit (7 GB).
    If current_mb is not provided, it measures the current usage.
    Returns True if within limits, False otherwise.
    Logs a warning if the limit is exceeded.
    """
    if current_mb is None:
        current_mb = get_memory_usage_mb()
    
    if current_mb > MEMORY_LIMIT_MB:
        logger.warning(
            f"Memory limit exceeded! Current: {current_mb:.2f} MB, "
            f"Limit: {MEMORY_LIMIT_MB:.2f} MB ({MEMORY_LIMIT_GB} GB). "
            f"Compliance with SC-005 violated."
        )
        return False
    
    logger.debug(f"Memory usage within limit: {current_mb:.2f} MB / {MEMORY_LIMIT_MB:.2f} MB")
    return True

@contextmanager
def timed_block(block_name: str = "Block") -> Generator[None, None, None]:
    """
    Context manager to log the execution time of a code block.
    """
    start_time = time.time()
    try:
        yield
    finally:
        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"Time elapsed for '{block_name}': {duration:.4f} seconds")

def timed_function(func: Callable) -> Callable:
    """
    Decorator to log the execution time of a function.
    """
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            end_time = time.time()
            duration = end_time - start_time
            logger.info(f"Time elapsed for '{func.__name__}': {duration:.4f} seconds")
    return wrapper

def log_exception(exc_type: type, exc_val: Exception, exc_tb: Any) -> None:
    """
    Logs a full traceback of an exception.
    """
    logger.error("An exception occurred:")
    logger.error("".join(traceback.format_exception(exc_type, exc_val, exc_tb)))

class MemoryTracker:
    """
    Tracks memory usage over a specific scope or operation.
    Logs the start, end, and delta of memory usage.
    Ensures compliance with SC-005 (7 GB limit) by checking limits at start and end.
    """
    def __init__(self, operation_name: str = "Operation"):
        self.operation_name = operation_name
        self.start_mb: float = 0.0
        self.end_mb: float = 0.0
        self.delta_mb: float = 0.0
        self._measured_start: bool = False
        self._measured_end: bool = False

    def start(self) -> None:
        """
        Records the starting memory usage.
        """
        try:
            self.start_mb = get_memory_usage_mb()
            self._measured_start = True
            logger.info(f"[MemoryTracker] {self.operation_name} started. "
                        f"Initial memory: {self.start_mb:.2f} MB")
            
            if not check_memory_limit(self.start_mb):
                logger.error(f"[MemoryTracker] {self.operation_name} started above memory limit. "
                             f"Aborting to prevent system instability.")
                raise MemoryError(f"Memory limit exceeded at start of {self.operation_name}")
        except RuntimeError as e:
            logger.warning(f"[MemoryTracker] Could not measure initial memory: {e}")

    def stop(self) -> None:
        """
        Records the ending memory usage, calculates delta, and logs the result.
        """
        try:
            if not self._measured_start:
                logger.warning(f"[MemoryTracker] start() was not called for {self.operation_name}. "
                               f"Measuring end memory only.")
            
            self.end_mb = get_memory_usage_mb()
            self._measured_end = True
            
            if self._measured_start:
                self.delta_mb = self.end_mb - self.start_mb
            
            logger.info(f"[MemoryTracker] {self.operation_name} finished. "
                        f"Final memory: {self.end_mb:.2f} MB, "
                        f"Delta: {self.delta_mb:.2f} MB")
            
            if not check_memory_limit(self.end_mb):
                logger.error(f"[MemoryTracker] {self.operation_name} finished above memory limit. "
                             f"SC-005 compliance check FAILED.")
        except RuntimeError as e:
            logger.warning(f"[MemoryTracker] Could not measure final memory: {e}")

    def __enter__(self) -> "MemoryTracker":
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()
        if exc_type is not None:
            log_exception(exc_type, exc_val, exc_tb)