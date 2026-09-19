import os
import sys
import logging

logger = logging.getLogger(__name__)

def get_memory_usage_mb() -> float:
    """
    Get current memory usage of the process in MB.
    Works on Linux, macOS, and Windows (with limitations).
    """
    if sys.platform.startswith('linux'):
        # Read from /proc/self/status
        try:
            with open('/proc/self/status', 'r') as f:
                for line in f:
                    if line.startswith('VmRSS:'):
                        # VmRSS is in kB
                        parts = line.split()
                        if len(parts) >= 2:
                            return float(parts[1]) / 1024.0
        except Exception as e:
            logger.warning(f"Could not read /proc/self/status: {e}")
    elif sys.platform == 'darwin':
        # macOS: use resource module
        try:
            import resource
            rusage = resource.getrusage(resource.RUSAGE_SELF)
            # ru_maxrss is in bytes on macOS
            return rusage.ru_maxrss / (1024 * 1024)
        except Exception as e:
            logger.warning(f"Could not get memory usage on macOS: {e}")
    elif sys.platform == 'win32':
        # Windows: use psutil if available, else fallback
        try:
            import psutil
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / (1024 * 1024)
        except ImportError:
            logger.warning("psutil not available on Windows. Memory check may be inaccurate.")
            return 0.0
        except Exception as e:
            logger.warning(f"Could not get memory usage on Windows: {e}")
    
    # Fallback: return 0 if detection fails
    logger.warning("Memory usage detection failed, returning 0.")
    return 0.0

def check_memory_limit(limit_mb: float = 2048.0) -> bool:
    """
    Check if current memory usage is below the limit.
    
    Args:
        limit_mb: Memory limit in MB.
        
    Returns:
        True if usage is below limit, False otherwise.
    """
    current = get_memory_usage_mb()
    if current > limit_mb:
        logger.error(f"Memory limit ({limit_mb} MB) exceeded. Current: {current} MB")
        return False
    return True
