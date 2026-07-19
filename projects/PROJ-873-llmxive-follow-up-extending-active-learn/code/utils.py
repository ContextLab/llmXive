import os
import signal
import sys
import time
import resource
import logging
from threading import Timer
from typing import Optional

logger = logging.getLogger(__name__)

# Constants from config.py to ensure consistency
RUNTIME_LIMIT_HOURS = 6
MEMORY_LIMIT_GB = 7
RUNTIME_LIMIT_SECONDS = RUNTIME_LIMIT_HOURS * 3600
MEMORY_LIMIT_BYTES = MEMORY_LIMIT_GB * 1024**3

class ResourceWatchdog:
    def __init__(self, timeout_seconds: Optional[float] = None, max_memory_mb: Optional[int] = None):
        self.timeout_seconds = timeout_seconds
        self.max_memory_mb = max_memory_mb
        self.timer: Optional[Timer] = None
        self.start_time: Optional[float] = None
        self._memory_check_interval = 10  # Check memory every 10 seconds
        self._memory_timer: Optional[Timer] = None

    def start(self):
        self.start_time = time.time()
        if self.timeout_seconds:
            self.timer = Timer(self.timeout_seconds, self._timeout_handler)
            self.timer.daemon = True
            self.timer.start()
            logger.info(f"Runtime watchdog started: {self.timeout_seconds}s limit")
        
        if self.max_memory_mb:
            # Set soft limit to max_memory_mb
            max_bytes = self.max_memory_mb * 1024 * 1024
            try:
                # Use RLIMIT_AS for address space limit (includes stack, heap, data)
                resource.setrlimit(resource.RLIMIT_AS, (max_bytes, max_bytes))
                logger.info(f"Memory watchdog started: {self.max_memory_mb}MB limit")
            except (ValueError, resource.error) as e:
                logger.warning(f"Could not set memory limit: {e}")

        # Start periodic memory check thread if limit is set
        if self.max_memory_mb:
            self._memory_timer = Timer(self._memory_check_interval, self._periodic_memory_check)
            self._memory_timer.daemon = True
            self._memory_timer.start()

    def stop(self):
        if self.timer:
            self.timer.cancel()
            self.timer = None
        if self._memory_timer:
            self._memory_timer.cancel()
            self._memory_timer = None
        logger.info("Resource watchdog stopped")

    def _timeout_handler(self):
        elapsed = time.time() - self.start_time if self.start_time else 0
        logger.error(f"Runtime limit exceeded: {elapsed:.2f}s. Terminating...")
        sys.exit(1)

    def _periodic_memory_check(self):
        """Periodically check memory usage and terminate if exceeded."""
        if self.max_memory_mb:
            try:
                usage = resource.getrusage(resource.RUSAGE_SELF)
                # ru_maxrss is in KB on Linux, MB on macOS
                if sys.platform == 'darwin':
                    usage_mb = usage.ru_maxrss
                else:
                    usage_mb = usage.ru_maxrss / 1024
                
                if usage_mb > self.max_memory_mb:
                    logger.error(f"Memory limit exceeded: {usage_mb:.2f}MB > {self.max_memory_mb}MB. Terminating...")
                    sys.exit(1)
            except Exception as e:
                logger.warning(f"Memory check failed: {e}")
        
        # Schedule next check if still running
        if self._memory_timer and self.max_memory_mb:
            self._memory_timer = Timer(self._memory_check_interval, self._periodic_memory_check)
            self._memory_timer.daemon = True
            self._memory_timer.start()

def enforce_resource_limits(config):
    """Enforce resource limits based on config.
    
    Args:
        config: PipelineConfig object with runtime_limit_seconds and memory_limit_bytes
               or runtime_limit_hours and memory_limit_mb attributes.
    
    Returns:
        ResourceWatchdog instance that is started and monitoring.
    """
    # Handle both attribute naming conventions
    if hasattr(config, 'runtime_limit_seconds'):
        timeout_seconds = config.runtime_limit_seconds
    elif hasattr(config, 'runtime_limit_hours'):
        timeout_seconds = config.runtime_limit_hours * 3600
    else:
        timeout_seconds = RUNTIME_LIMIT_SECONDS
    
    if hasattr(config, 'memory_limit_bytes'):
        max_memory_mb = config.memory_limit_bytes / (1024 * 1024)
    elif hasattr(config, 'memory_limit_mb'):
        max_memory_mb = config.memory_limit_mb
    else:
        max_memory_mb = MEMORY_LIMIT_GB * 1024
    
    watchdog = ResourceWatchdog(
        timeout_seconds=timeout_seconds,
        max_memory_mb=int(max_memory_mb)
    )
    watchdog.start()
    return watchdog