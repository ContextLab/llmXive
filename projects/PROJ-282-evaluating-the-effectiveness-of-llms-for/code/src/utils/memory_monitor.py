"""
Memory monitoring utilities for the LLMXive research pipeline.

Provides a context manager and utility functions to track runtime memory usage,
enforce memory constraints, and trigger batch size reduction when approaching
high thresholds.

Implements FR-002 (Runtime Constraints) and SC-005 (Memory Safety).
"""
import os
import gc
import logging
from typing import Optional, Callable, TypeVar, ContextManager
from datetime import datetime
import resource

from src.utils.logger import get_logger

# Type variable for generic context manager usage
T = TypeVar('T')

# Constants
MEMORY_WARNING_THRESHOLD = 0.85  # 85% of available RAM
MEMORY_CRITICAL_THRESHOLD = 0.95  # 95% of available RAM
MEMORY_CHECK_INTERVAL_SECONDS = 1.0

# Global logger instance
_logger: Optional[logging.Logger] = None

def _get_logger() -> logging.Logger:
    """Get or create the project logger."""
    global _logger
    if _logger is None:
        _logger = get_logger("memory_monitor")
    return _logger

def get_available_ram_gb() -> float:
    """
    Get the total available RAM in GB on the current system.
    
    Returns:
        float: Total RAM in gigabytes.
        
    Raises:
        OSError: If unable to determine system memory (non-Unix systems).
    """
    try:
        # Use resource module for Unix-like systems
        # Note: resource.getrlimit(resource.RLIMIT_AS) gives virtual memory limits
        # For physical RAM, we use the system's total memory
        if os.name == 'posix':
            # Read from /proc/meminfo on Linux
            meminfo_path = '/proc/meminfo'
            if os.path.exists(meminfo_path):
                with open(meminfo_path, 'r') as f:
                    for line in f:
                        if line.startswith('MemTotal:'):
                            # Convert kB to GB
                            mem_kb = int(line.split()[1])
                            return mem_kb / (1024 * 1024)
            # Fallback: use resource limits if /proc/meminfo not available
            _, soft_limit = resource.getrlimit(resource.RLIMIT_AS)
            if soft_limit != resource.RLIM_INFINITY:
                return soft_limit / (1024 * 1024 * 1024)
        else:
            # Windows/Mac: Try to use resource module (may not be available)
            _, soft_limit = resource.getrlimit(resource.RLIMIT_AS)
            if soft_limit != resource.RLIM_INFINITY:
                return soft_limit / (1024 * 1024 * 1024)
        
        # Ultimate fallback: estimate based on typical systems
        # This is a last resort and should log a warning
        logger = _get_logger()
        logger.warning("Could not determine system RAM, assuming 8GB default")
        return 8.0
        
    except Exception as e:
        logger = _get_logger()
        logger.warning(f"Error determining system RAM: {e}, assuming 8GB default")
        return 8.0

def get_current_memory_usage_gb() -> float:
    """
    Get the current memory usage of the process in GB.
    
    Returns:
        float: Current memory usage in gigabytes.
    """
    try:
        if os.name == 'posix':
            # Get memory usage from resource module
            usage = resource.getrusage(resource.RUSAGE_SELF)
            # ru_maxrss is in KB on Linux, bytes on some systems
            # Normalize to GB
            maxrss_kb = usage.ru_maxrss
            # On Linux, ru_maxrss is in KB
            return maxrss_kb / (1024 * 1024)
        else:
            # Windows: Try psutil if available, else fallback
            try:
                import psutil
                process = psutil.Process(os.getpid())
                return process.memory_info().rss / (1024 * 1024 * 1024)
            except ImportError:
                # Fallback to resource (may not work on Windows)
                usage = resource.getrusage(resource.RUSAGE_SELF)
                return usage.ru_maxrss / (1024 * 1024 * 1024)
    except Exception as e:
        logger = _get_logger()
        logger.warning(f"Error getting current memory usage: {e}")
        return 0.0

def get_memory_usage_ratio() -> float:
    """
    Get the current memory usage as a ratio of total available RAM.
    
    Returns:
        float: Ratio between 0.0 and 1.0.
    """
    total_ram = get_available_ram_gb()
    current_usage = get_current_memory_usage_gb()
    return current_usage / total_ram if total_ram > 0 else 0.0

def check_memory_constraint(threshold: float = MEMORY_WARNING_THRESHOLD) -> bool:
    """
    Check if current memory usage exceeds a given threshold.
    
    Args:
        threshold: Memory usage ratio threshold (0.0 to 1.0). Default is 0.85.
        
    Returns:
        bool: True if memory usage exceeds threshold, False otherwise.
    """
    ratio = get_memory_usage_ratio()
    logger = _get_logger()
    
    if ratio > threshold:
        logger.warning(
            f"Memory usage ({ratio:.2%}) exceeds threshold ({threshold:.2%})",
            extra={
                'memory_ratio': ratio,
                'threshold': threshold,
                'current_gb': get_current_memory_usage_gb(),
                'total_gb': get_available_ram_gb()
            }
        )
        return True
    
    return False

def force_gc() -> None:
    """Force garbage collection to free up memory."""
    logger = _get_logger()
    logger.debug("Forcing garbage collection")
    gc.collect()
    gc.collect()
    gc.collect()  # Triple collection for thorough cleanup

class MemoryMonitor(ContextManager):
    """
    Context manager to monitor memory usage during a code block.
    
    Automatically checks memory usage at intervals and triggers garbage
    collection if usage exceeds warning threshold. Can optionally reduce
    batch size if critical threshold is approached.
    
    Attributes:
        threshold_warning: Warning threshold (default 0.85)
        threshold_critical: Critical threshold (default 0.95)
        check_interval: Seconds between checks (default 1.0)
        batch_size: Current batch size (can be reduced if critical)
        min_batch_size: Minimum allowed batch size
    """
    
    def __init__(
        self,
        threshold_warning: float = MEMORY_WARNING_THRESHOLD,
        threshold_critical: float = MEMORY_CRITICAL_THRESHOLD,
        check_interval: float = MEMORY_CHECK_INTERVAL_SECONDS,
        batch_size: int = 32,
        min_batch_size: int = 1
    ):
        """
        Initialize the memory monitor.
        
        Args:
            threshold_warning: Warning threshold (0.0 to 1.0)
            threshold_critical: Critical threshold (0.0 to 1.0)
            check_interval: Seconds between memory checks
            batch_size: Initial batch size to monitor
            min_batch_size: Minimum batch size to allow
        """
        self.threshold_warning = threshold_warning
        self.threshold_critical = threshold_critical
        self.check_interval = check_interval
        self.batch_size = batch_size
        self.min_batch_size = min_batch_size
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.max_ratio_observed: float = 0.0
        self._logger = _get_logger()
        
    def __enter__(self) -> 'MemoryMonitor':
        """Enter the context, start monitoring."""
        self.start_time = datetime.now()
        self._logger.info(
            "Memory monitoring started",
            extra={
                'batch_size': self.batch_size,
                'threshold_warning': self.threshold_warning,
                'threshold_critical': self.threshold_critical
            }
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the context, log final statistics."""
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds() if self.start_time else 0
        
        self._logger.info(
            "Memory monitoring completed",
            extra={
                'duration_seconds': duration,
                'final_batch_size': self.batch_size,
                'max_memory_ratio': self.max_ratio_observed,
                'peak_memory_gb': get_current_memory_usage_gb(),
                'total_memory_gb': get_available_ram_gb()
            }
        )
        
        # Force garbage collection on exit
        force_gc()
        
        # Don't suppress exceptions
        return False
    
    def check_and_adjust(self) -> int:
        """
        Check current memory usage and adjust batch size if necessary.
        
        Returns:
            int: The current (possibly adjusted) batch size.
        """
        ratio = get_memory_usage_ratio()
        self.max_ratio_observed = max(self.max_ratio_observed, ratio)
        
        if ratio > self.threshold_critical:
            self._logger.critical(
                f"CRITICAL: Memory usage at {ratio:.2%}",
                extra={
                    'current_ratio': ratio,
                    'current_batch_size': self.batch_size,
                    'action': 'reducing_batch_size'
                }
            )
            # Reduce batch size by half, but not below minimum
            new_batch_size = max(self.min_batch_size, self.batch_size // 2)
            if new_batch_size < self.batch_size:
                self.batch_size = new_batch_size
                self._logger.info(
                    f"Reduced batch size to {self.batch_size} due to critical memory usage",
                    extra={'new_batch_size': self.batch_size}
                )
            force_gc()
            
        elif ratio > self.threshold_warning:
            self._logger.warning(
                f"WARNING: Memory usage at {ratio:.2%}",
                extra={
                    'current_ratio': ratio,
                    'current_batch_size': self.batch_size,
                    'action': 'monitoring'
                }
            )
            # Consider reducing batch size if approaching critical
            if ratio > 0.90:
                new_batch_size = max(self.min_batch_size, self.batch_size * 3 // 4)
                if new_batch_size < self.batch_size:
                    self.batch_size = new_batch_size
                    self._logger.info(
                        f"Preemptively reduced batch size to {self.batch_size}",
                        extra={'new_batch_size': self.batch_size}
                    )
        
        return self.batch_size

def monitor_batch_processing(
    batch_size: int,
    min_batch_size: int = 1,
    threshold_warning: float = MEMORY_WARNING_THRESHOLD,
    threshold_critical: float = MEMORY_CRITICAL_THRESHOLD
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to monitor memory usage during batch processing.
    
    Automatically adjusts batch size if memory constraints are approached.
    
    Args:
        batch_size: Initial batch size
        min_batch_size: Minimum allowed batch size
        threshold_warning: Warning threshold
        threshold_critical: Critical threshold
        
    Returns:
        Callable: Decorator function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args, **kwargs) -> T:
            monitor = MemoryMonitor(
                threshold_warning=threshold_warning,
                threshold_critical=threshold_critical,
                batch_size=batch_size,
                min_batch_size=min_batch_size
            )
            
            with monitor:
                # Check memory before processing
                current_batch = monitor.check_and_adjust()
                
                # Execute function with adjusted batch size
                result = func(*args, current_batch, **kwargs)
                
                # Check memory after processing
                monitor.check_and_adjust()
                
                return result
        
        return wrapper
    
    return decorator

def get_memory_snapshot() -> dict:
    """
    Get a snapshot of current memory state.
    
    Returns:
        dict: Memory snapshot with current usage, total RAM, and ratio.
    """
    return {
        'timestamp': datetime.now().isoformat(),
        'current_memory_gb': get_current_memory_usage_gb(),
        'total_memory_gb': get_available_ram_gb(),
        'usage_ratio': get_memory_usage_ratio(),
        'pid': os.getpid()
    }

# Export public API
__all__ = [
    'MemoryMonitor',
    'get_available_ram_gb',
    'get_current_memory_usage_gb',
    'get_memory_usage_ratio',
    'check_memory_constraint',
    'force_gc',
    'monitor_batch_processing',
    'get_memory_snapshot',
    'MEMORY_WARNING_THRESHOLD',
    'MEMORY_CRITICAL_THRESHOLD'
]
