"""
Utility functions for resource monitoring and enforcement.
Implements watchdog/signal handler to terminate pipeline if runtime or memory limits are exceeded.
Serves FR-006 enforcement.
"""
import os
import signal
import sys
import time
import resource
import logging
from typing import Optional, Callable

class ResourceWatchdog:
    """
    Monitors resource usage and triggers termination if limits are exceeded.
    Implements watchdog/signal handler for FR-006.
    """
    def __init__(self, max_runtime_seconds: int, max_memory_mb: int):
        self.max_runtime = max_runtime_seconds
        self.max_memory = max_memory_mb * 1024 * 1024  # Convert to bytes
        self.start_time = time.time()
        self.logger = logging.getLogger(__name__)
        self._alarm_set = False

        # Setup signal handler for timeout
        if hasattr(signal, 'SIGALRM'):
            # Store old handler to restore later if needed
            self._old_handler = signal.signal(signal.SIGALRM, self._timeout_handler)
            signal.alarm(self.max_runtime)
            self._alarm_set = True
            self.logger.info(f"Watchdog started: Runtime limit {self.max_runtime}s, Memory limit {max_memory_mb}MB")
        else:
            self.logger.warning("SIGALRM not available on this platform. Runtime limit not enforced via signal.")

    def _timeout_handler(self, signum, frame):
        self.logger.error(f"Runtime limit of {self.max_runtime}s exceeded. Terminating.")
        # Restore old handler to prevent recursive alarm if possible
        if hasattr(signal, 'SIGALRM'):
            signal.signal(signal.SIGALRM, self._old_handler)
        sys.exit(1)

    def check_memory(self) -> bool:
        """Check current memory usage against limit. Returns False if limit exceeded."""
        try:
            usage = resource.getrusage(resource.RUSAGE_SELF)
            # ru_maxrss is in KB on Linux, convert to bytes
            current_mem = usage.ru_maxrss * 1024
            if current_mem > self.max_memory:
                self.logger.error(f"Memory limit exceeded: {current_mem/1024/1024:.1f}MB > {self.max_memory/1024/1024:.1f}MB")
                sys.exit(1)
                return False
        except Exception as e:
            self.logger.warning(f"Could not check memory: {e}")
        return True

    def check_runtime(self) -> bool:
        """Check if runtime limit exceeded. Returns False if limit exceeded."""
        elapsed = time.time() - self.start_time
        if elapsed > self.max_runtime:
            self.logger.error(f"Runtime limit exceeded: {elapsed:.1f}s > {self.max_runtime}s")
            sys.exit(1)
            return False
        return True

    def stop(self):
        """Stop the watchdog."""
        if self._alarm_set:
            signal.alarm(0)
            if hasattr(signal, 'SIGALRM'):
                signal.signal(signal.SIGALRM, self._old_handler)
            self._alarm_set = False
            self.logger.info("Watchdog stopped.")

def enforce_resource_limits(max_runtime: int, max_memory_mb: int) -> ResourceWatchdog:
    """
    Convenience function to start a watchdog and check limits periodically.
    Returns the watchdog instance for manual checks or context use.
    """
    return ResourceWatchdog(max_runtime, max_memory_mb)

# Global watchdog instance for periodic checks
_global_watchdog: Optional[ResourceWatchdog] = None

def init_watchdog(max_runtime_hours: float = 6.0, max_memory_gb: float = 7.0):
    """
    Initialize the global watchdog with limits from config.
    Serves FR-006 enforcement.
    """
    global _global_watchdog
    max_runtime_seconds = int(max_runtime_hours * 3600)
    max_memory_mb = int(max_memory_gb * 1024)
    _global_watchdog = enforce_resource_limits(max_runtime_seconds, max_memory_mb)
    return _global_watchdog

def check_limits_periodically():
    """
    Periodically check resource limits. Should be called in long-running loops.
    """
    global _global_watchdog
    if _global_watchdog:
        _global_watchdog.check_memory()
        _global_watchdog.check_runtime()

def stop_watchdog():
    """Stop the global watchdog."""
    global _global_watchdog
    if _global_watchdog:
        _global_watchdog.stop()
        _global_watchdog = None