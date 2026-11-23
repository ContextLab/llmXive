"""
Memory monitoring utilities for enforcing resource limits.

Implements FR-008: Memory and time limit enforcement with graceful degradation.
"""
import os
import sys
import time
import logging
import signal
from typing import Optional, Callable, Any
import threading
from functools import wraps

logger = logging.getLogger(__name__)


def check_limits(max_memory_mb: int = 7000, max_time_seconds: int = 21600) -> bool:
    """
    Check if current resource usage is within limits.
    
    Args:
        max_memory_mb: Maximum allowed memory in MB (default 7GB)
        max_time_seconds: Maximum allowed time in seconds (default 6 hours)
        
    Returns:
        True if within limits, False otherwise
    """
    # Check memory usage
    try:
        # Try to get memory usage via psutil if available
        try:
            import psutil
            process = psutil.Process(os.getpid())
            mem_info = process.memory_info()
            current_memory_mb = mem_info.rss / (1024 * 1024)
            
            if current_memory_mb > max_memory_mb:
                logger.error(f"Memory limit exceeded: {current_memory_mb:.1f}MB > {max_memory_mb}MB")
                return False
        except ImportError:
            # Fallback: try /proc on Linux
            if sys.platform.startswith('linux'):
                with open(f'/proc/{os.getpid()}/statm', 'r') as f:
                    statm = f.read().split()
                    # Second column is RSS in pages
                    page_size = os.sysconf('SC_PAGE_SIZE')
                    current_memory_mb = (int(statm[1]) * page_size) / (1024 * 1024)
                    
                    if current_memory_mb > max_memory_mb:
                        logger.error(f"Memory limit exceeded: {current_memory_mb:.1f}MB > {max_memory_mb}MB")
                        return False
            
        logger.debug(f"Current memory usage: {current_memory_mb:.1f}MB / {max_memory_mb}MB")
        
    except Exception as e:
        logger.warning(f"Could not check memory usage: {e}")
    
    return True


def graceful_exit(message: str = "Resource limits exceeded"):
    """
    Gracefully exit the program with a clear error message.
    
    Args:
        message: Error message to log before exiting
    """
    logger.critical(f"{message}. Terminating execution.")
    sys.exit(1)


class limit_enforcer:
    """
    Context manager and decorator for enforcing resource limits.
    
    Usage as context manager:
        with limit_enforcer(max_memory_mb=7000, max_time_seconds=3600):
            # code that might exceed limits
            pass
    
    Usage as decorator:
        @limit_enforcer(max_memory_mb=7000, max_time_seconds=3600)
        def my_function():
            pass
    """
    
    def __init__(self, max_memory_mb: int = 7000, max_time_seconds: int = 21600):
        self.max_memory_mb = max_memory_mb
        self.max_time_seconds = max_time_seconds
        self.start_time: Optional[float] = None
        self.thread: Optional[threading.Thread] = None
        self.limit_exceeded = False
        
    def _check_memory(self):
        """Background thread to monitor memory usage."""
        while not self.limit_exceeded:
            if not check_limits(self.max_memory_mb, self.max_time_seconds):
                self.limit_exceeded = True
                graceful_exit(f"Memory limit exceeded ({self.max_memory_mb}MB)")
            time.sleep(1)  # Check every second
            
    def _check_time(self):
        """Background thread to monitor elapsed time."""
        while not self.limit_exceeded:
            if self.start_time and (time.time() - self.start_time) > self.max_time_seconds:
                self.limit_exceeded = True
                graceful_exit(f"Time limit exceeded ({self.max_time_seconds}s)")
            time.sleep(1)  # Check every second
    
    def __enter__(self):
        self.start_time = time.time()
        self.limit_exceeded = False
        
        # Start monitoring threads
        self.memory_thread = threading.Thread(target=self._check_memory, daemon=True)
        self.time_thread = threading.Thread(target=self._check_time, daemon=True)
        
        self.memory_thread.start()
        self.time_thread.start()
        
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            elapsed = time.time() - self.start_time
            logger.info(f"Execution completed in {elapsed:.1f} seconds")
        
        # Stop monitoring
        self.limit_exceeded = True
        return False
    
    def __call__(self, func: Callable):
        """Decorator usage."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            with self:
                return func(*args, **kwargs)
        return wrapper


def enforce_limits(func: Callable) -> Callable:
    """
    Decorator to enforce resource limits on a function.
    
    Args:
        func: Function to wrap
        
    Returns:
        Wrapped function with limit enforcement
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        with limit_enforcer():
            return func(*args, **kwargs)
    return wrapper
